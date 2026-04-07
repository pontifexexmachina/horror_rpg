from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from dead_by_dawn_sim.combat_support import attack_weapon, has_condition
from dead_by_dawn_sim.dice import DiceRoller
from dead_by_dawn_sim.engine_rolls import (
    ContestResult,
    RollMode,
    RollResult,
    difficulty_value,
    roll_check,
    roll_contest,
)
from dead_by_dawn_sim.engine_state import (
    apply_damage,
    heal_target,
    remove_condition,
    run_stress_test,
    transition_actor_state,
    uses_stress_track,
)
from dead_by_dawn_sim.rules import (
    ActionDefinition,
    ApplyAttackModifierStep,
    ApplyConditionStep,
    ApplyHealingStep,
    ApplyStressStep,
    AttackEffect,
    AttackRollStep,
    CheckRollStep,
    ClearConditionStep,
    ContestRollStep,
    MoveTargetStep,
    Ruleset,
    WeaponDefinition,
    action_has_heal_steps,
    attack_effect_from_step,
)
from dead_by_dawn_sim.state import (
    ActorState,
    ConditionState,
    EncounterState,
    TalentState,
    append_event,
    area_has_tag,
    can_enter_area,
    connected_area_ids,
    synchronize_engagements,
    update_actor,
)

RANGED_SKILLS = {"shoot"}


@dataclass(frozen=True)
class ActionResolutionContext:
    state: EncounterState
    actor: ActorState
    target: ActorState
    action: ActionDefinition
    roller: DiceRoller
    ruleset: Ruleset
    push: bool
    destination_area: str | None
    roll_mode: RollMode

    @classmethod
    def build(
        cls,
        *,
        state: EncounterState,
        actor: ActorState,
        target: ActorState,
        action: ActionDefinition,
        roller: DiceRoller,
        ruleset: Ruleset,
        push: bool,
        destination_area: str | None,
    ) -> ActionResolutionContext:
        return cls(
            state=state,
            actor=actor,
            target=target,
            action=action,
            roller=roller,
            ruleset=ruleset,
            push=push,
            destination_area=destination_area,
            roll_mode=roll_mode_for_action(action, actor, target),
        )

    def with_state(self, state: EncounterState) -> ActionResolutionContext:
        actor = state.actor(self.actor.actor_id)
        target = state.actor(self.target.actor_id)
        return replace(self, state=state, actor=actor, target=target)


def _effective_attack_modifier(actor: ActorState, ruleset: Ruleset) -> int:
    modifier = 0
    for condition in actor.conditions:
        modifier += ruleset.conditions[condition.id].attack_modifier
    return modifier


def _spend_attack_resource(actor: ActorState, effect: AttackEffect, ruleset: Ruleset) -> ActorState:
    weapon = attack_weapon(effect, actor, ruleset)
    if weapon is None or weapon.ammo_kind is None:
        return actor
    current = actor.ammo.get(weapon.ammo_kind, 0)
    if current <= 0:
        raise ValueError(f"Actor {actor.actor_id} attempted a ranged attack without ammo.")
    next_ammo = dict(actor.ammo)
    next_ammo[weapon.ammo_kind] = current - 1
    return replace(actor, ammo=next_ammo)


def _spend_bandage(actor: ActorState) -> ActorState:
    if actor.bandages <= 0:
        raise ValueError(f"Actor {actor.actor_id} attempted first aid without bandages.")
    return replace(actor, bandages=actor.bandages - 1)


def _ranged_cover_bonus(state: EncounterState, actor: ActorState, target: ActorState) -> int:
    if actor.area_id == target.area_id:
        return 0
    return 1 if area_has_tag(state, target.area_id, "cover_rich") else 0


def _ranged_concealment_penalty(
    state: EncounterState, actor: ActorState, target: ActorState
) -> int:
    if actor.area_id == target.area_id:
        return 0
    return -1 if area_has_tag(state, target.area_id, "dark") else 0


def roll_mode_for_action(
    action: ActionDefinition,
    actor: ActorState,
    target: ActorState,
) -> RollMode:
    swing = 0
    procedure = action.procedure
    if procedure is not None and any(isinstance(step, AttackRollStep) for step in procedure.steps):
        if has_condition(actor, "inspired") or has_condition(actor, "feinting"):
            swing += 1
        if has_condition(target, "prone"):
            swing += 1
    if action.range in {"engaged", "enemy", "far", "near"}:
        for condition in actor.conditions:
            if condition.id != "rattled":
                continue
            if condition.source_actor_id is None or target.actor_id != condition.source_actor_id:
                swing -= 1
    if swing > 0:
        return "advantage"
    if swing < 0:
        return "disadvantage"
    return "normal"


def _consume_attack_conditions(actor: ActorState) -> ActorState:
    actor = remove_condition(actor, "inspired")
    return remove_condition(actor, "feinting")


def attack_modifier_and_difficulty(
    state: EncounterState,
    actor: ActorState,
    target: ActorState,
    effect: AttackEffect,
    ruleset: Ruleset,
) -> tuple[int, int]:
    modifier = actor.stats[effect.stat] + actor.skills.get(effect.skill, 0)
    modifier += _effective_attack_modifier(actor, ruleset)
    difficulty = target.defense
    if effect.skill in RANGED_SKILLS:
        modifier += _ranged_concealment_penalty(state, actor, target)
        difficulty += _ranged_cover_bonus(state, actor, target)
    return modifier, difficulty


def _effect_modifier(actor: ActorState, stat: Literal["might", "speed", "wits"], skill: str) -> int:
    return actor.stats[stat] + actor.skills.get(skill, 0)


def _resolve_effect_check(
    *,
    actor: ActorState,
    stat: Literal["might", "speed", "wits"],
    skill: str,
    difficulty_name: str,
    roller: DiceRoller,
    ruleset: Ruleset,
    push: bool,
    roll_mode: RollMode,
) -> RollResult:
    return roll_check(
        roller=roller,
        ruleset=ruleset,
        modifier=_effect_modifier(actor, stat, skill),
        difficulty=difficulty_value(ruleset, difficulty_name),
        push=push,
        roll_mode=roll_mode,
    )


def _resolve_effect_contest(
    *,
    actor: ActorState,
    target: ActorState,
    stat: Literal["might", "speed", "wits"],
    skill: str,
    defense_stat: Literal["might", "speed", "wits"],
    roller: DiceRoller,
    ruleset: Ruleset,
    push: bool,
    roll_mode: RollMode,
) -> ContestResult:
    return roll_contest(
        roller=roller,
        ruleset=ruleset,
        attacker_modifier=_effect_modifier(actor, stat, skill),
        defender_modifier=target.stats[defense_stat],
        push=push,
        roll_mode=roll_mode,
    )


def _append_condition(
    target: ActorState,
    condition_id: str,
    rounds_remaining: int,
    *,
    source_actor_id: str | None = None,
) -> ActorState:
    return replace(
        target,
        conditions=(
            *target.conditions,
            ConditionState(
                id=condition_id,
                rounds_remaining=rounds_remaining,
                source_actor_id=source_actor_id,
            ),
        ),
    )


def apply_attack_hit(
    state: EncounterState,
    *,
    target: ActorState,
    weapon: WeaponDefinition,
    roller: DiceRoller,
    ruleset: Ruleset,
    critical: bool,
    event: str,
) -> EncounterState:
    damage_roll = roller.roll_d6(1)[0]
    damage = weapon.damage_die if critical else min(damage_roll, weapon.damage_die)
    updated_target = apply_damage(target, damage, ruleset)
    if "bleed" in weapon.tags:
        updated_target = _append_condition(updated_target, "bleeding", 3)
    state = update_actor(state, updated_target)
    return append_event(state, event.format(damage=damage))


def _apply_rattled(
    state: EncounterState,
    *,
    actor: ActorState,
    target: ActorState,
    duration_rounds: int,
) -> EncounterState:
    updated_target = _append_condition(
        target,
        "rattled",
        duration_rounds,
        source_actor_id=actor.actor_id,
    )
    state = update_actor(state, updated_target)
    return append_event(state, f"{actor.actor_id} rattles {target.actor_id}'s aim.")


def _move_target(
    state: EncounterState,
    target: ActorState,
    destination_area: str,
) -> EncounterState:
    moved = update_actor(state, replace(target, area_id=destination_area, engaged_with=frozenset()))
    return synchronize_engagements(moved)


@dataclass(frozen=True)
class ProcedureResolution:
    state: EncounterState
    actor: ActorState
    target: ActorState
    last_roll: RollResult | ContestResult | None = None

    @classmethod
    def build(cls, ctx: ActionResolutionContext) -> ProcedureResolution:
        return cls(state=ctx.state, actor=ctx.actor, target=ctx.target)

    def with_state(
        self,
        state: EncounterState,
        *,
        actor_id: str,
        target_id: str,
        last_roll: RollResult | ContestResult | None = None,
    ) -> ProcedureResolution:
        return ProcedureResolution(
            state=state,
            actor=state.actor(actor_id),
            target=state.actor(target_id),
            last_roll=self.last_roll if last_roll is None else last_roll,
        )


def _procedure_recipient(resolution: ProcedureResolution, target_name: str) -> ActorState:
    if target_name == "self":
        return resolution.actor
    return resolution.target


def _procedure_result_applies(
    last_roll: RollResult | ContestResult | None,
    when: Literal["always", "success", "critical"],
) -> bool:
    if when == "always":
        return True
    if last_roll is None or not last_roll.is_success:
        return False
    if when == "success":
        return True
    return last_roll.is_critical


def _auto_critical_heal_result(
    ctx: ActionResolutionContext, actor: ActorState
) -> tuple[EncounterState, ActorState, RollResult]:
    updated_actor = replace(
        actor,
        talent_state=TalentState(used=actor.talent_state.used | {"healing_hands"}),
    )
    state = update_actor(ctx.state, updated_actor)
    result = RollResult(kept=[6, 6], total=999, is_success=True, is_critical=True)
    return state, updated_actor, result


def _run_check_step(
    ctx: ActionResolutionContext,
    resolution: ProcedureResolution,
    step: CheckRollStep,
) -> ProcedureResolution:
    actor = resolution.actor
    state = resolution.state
    if ctx.action.id == "first_aid":
        actor = _spend_bandage(actor)
        state = update_actor(state, actor)
    if (
        action_has_heal_steps(ctx.action)
        and "healing_hands" in actor.talent_ids
        and "healing_hands" not in actor.talent_state.used
    ):
        state, actor, result = _auto_critical_heal_result(ctx, actor)
        return resolution.with_state(
            state,
            actor_id=actor.actor_id,
            target_id=resolution.target.actor_id,
            last_roll=result,
        )
    result = _resolve_effect_check(
        actor=actor,
        stat=step.stat,
        skill=step.skill,
        difficulty_name=step.difficulty,
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    return resolution.with_state(
        state,
        actor_id=actor.actor_id,
        target_id=resolution.target.actor_id,
        last_roll=result,
    )


def _run_contest_step(
    ctx: ActionResolutionContext,
    resolution: ProcedureResolution,
    step: ContestRollStep,
) -> ProcedureResolution:
    result = _resolve_effect_contest(
        actor=resolution.actor,
        target=resolution.target,
        stat=step.stat,
        skill=step.skill,
        defense_stat=step.defense_stat,
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    return resolution.with_state(
        resolution.state,
        actor_id=resolution.actor.actor_id,
        target_id=resolution.target.actor_id,
        last_roll=result,
    )


def _run_attack_step(
    ctx: ActionResolutionContext,
    resolution: ProcedureResolution,
    step: AttackRollStep,
) -> ProcedureResolution:
    effect = attack_effect_from_step(step)
    weapon = attack_weapon(effect, resolution.actor, ctx.ruleset)
    if weapon is None:
        raise ValueError(f"Actor {resolution.actor.actor_id} attempted an attack without a weapon.")
    actor = (
        _spend_attack_resource(resolution.actor, effect, ctx.ruleset)
        if effect.skill == "shoot"
        else resolution.actor
    )
    state = update_actor(resolution.state, actor)
    modifier, difficulty = attack_modifier_and_difficulty(
        state, actor, resolution.target, effect, ctx.ruleset
    )
    result = roll_check(
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        modifier=modifier,
        difficulty=difficulty,
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    actor_after = _consume_attack_conditions(state.actor(actor.actor_id))
    state = update_actor(state, actor_after)
    if result.is_success:
        state = apply_attack_hit(
            state,
            target=state.actor(resolution.target.actor_id),
            weapon=weapon,
            roller=ctx.roller,
            ruleset=ctx.ruleset,
            critical=result.is_critical,
            event=f"{resolution.actor.actor_id} hits {resolution.target.actor_id} for {{damage}}.",
        )
    else:
        state = append_event(state, f"{resolution.actor.actor_id} misses {resolution.target.actor_id}.")
    return resolution.with_state(
        state,
        actor_id=resolution.actor.actor_id,
        target_id=resolution.target.actor_id,
        last_roll=result,
    )


def _run_apply_condition_step(
    resolution: ProcedureResolution,
    step: ApplyConditionStep,
) -> ProcedureResolution:
    if not _procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    recipient = _procedure_recipient(resolution, step.target)
    updated = _append_condition(recipient, step.condition_id, step.duration_rounds)
    state = update_actor(resolution.state, updated)
    return resolution.with_state(
        state,
        actor_id=resolution.actor.actor_id,
        target_id=resolution.target.actor_id,
    )


def _run_heal_step(
    ctx: ActionResolutionContext,
    resolution: ProcedureResolution,
    step: ApplyHealingStep,
) -> ProcedureResolution:
    if not _procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    recipient = _procedure_recipient(resolution, step.target)
    updated = heal_target(recipient, step.amount, ctx.ruleset)
    state = update_actor(resolution.state, updated)
    return resolution.with_state(
        state,
        actor_id=resolution.actor.actor_id,
        target_id=resolution.target.actor_id,
    )


def _run_stress_step(
    ctx: ActionResolutionContext,
    resolution: ProcedureResolution,
    step: ApplyStressStep,
) -> ProcedureResolution:
    if not _procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    recipient = _procedure_recipient(resolution, step.target)
    if not uses_stress_track(recipient):
        return resolution
    updated = transition_actor_state(replace(recipient, stress=recipient.stress + step.amount), ctx.ruleset)
    state = update_actor(resolution.state, updated)
    return resolution.with_state(
        state,
        actor_id=resolution.actor.actor_id,
        target_id=resolution.target.actor_id,
    )


def _run_attack_modifier_step(
    ctx: ActionResolutionContext,
    resolution: ProcedureResolution,
    step: ApplyAttackModifierStep,
) -> ProcedureResolution:
    if not _procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    if step.target != "target":
        raise ValueError("Attack modifier procedure steps currently only support target recipients.")
    state = _apply_rattled(
        resolution.state,
        actor=resolution.actor,
        target=resolution.target,
        duration_rounds=step.duration_rounds,
    )
    return resolution.with_state(
        state,
        actor_id=resolution.actor.actor_id,
        target_id=resolution.target.actor_id,
    )


def _validate_move_destination(ctx: ActionResolutionContext) -> str:
    if ctx.destination_area is None:
        raise ValueError(f"Action {ctx.action.id} requires a destination area.")
    if ctx.destination_area not in connected_area_ids(ctx.state, ctx.target.area_id):
        raise ValueError(
            f"Action {ctx.action.id} cannot move {ctx.target.actor_id} to {ctx.destination_area}."
        )
    if not can_enter_area(ctx.state, ctx.destination_area):
        raise ValueError(
            f"Action {ctx.action.id} cannot move {ctx.target.actor_id} into a full area."
        )
    return ctx.destination_area


def _run_clear_condition_step(
    resolution: ProcedureResolution,
    step: ClearConditionStep,
) -> ProcedureResolution:
    if not _procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    recipient = _procedure_recipient(resolution, step.target)
    updated = remove_condition(recipient, step.condition_id)
    state = update_actor(resolution.state, updated)
    return resolution.with_state(
        state,
        actor_id=resolution.actor.actor_id,
        target_id=resolution.target.actor_id,
    )


def _run_move_target_step(
    ctx: ActionResolutionContext,
    resolution: ProcedureResolution,
    step: MoveTargetStep,
) -> ProcedureResolution:
    if not _procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    if step.destination != "choice":
        raise ValueError(f"Unsupported move destination mode {step.destination}.")
    destination_area = _validate_move_destination(ctx)
    state = _move_target(resolution.state, resolution.target, destination_area)
    return resolution.with_state(
        state,
        actor_id=resolution.actor.actor_id,
        target_id=resolution.target.actor_id,
    )


def _finalize_procedure_action(
    ctx: ActionResolutionContext,
    before: ProcedureResolution,
    after: ProcedureResolution,
) -> EncounterState:
    last_roll = after.last_roll
    actor_id = before.actor.actor_id
    target_id = before.target.actor_id
    state = after.state
    if ctx.action.id in {"attack", "brawl_attack", "unarmed_attack", "taunt"}:
        state = after.state
    elif ctx.action.id in {"first_aid", "grit"}:
        if last_roll is None or not last_roll.is_success:
            state = append_event(after.state, f"{actor_id} fails to heal {target_id}.")
        else:
            healed_amount = after.target.hp - before.target.hp
            state = append_event(after.state, f"{actor_id} heals {target_id} for {healed_amount}.")
    elif ctx.action.id == "rally":
        if last_roll is None or not last_roll.is_success:
            state = append_event(after.state, f"{actor_id} fails to rally {target_id}.")
        else:
            state = append_event(after.state, f"{actor_id} rallies {target_id}.")
    elif ctx.action.id == "shriek":
        if last_roll is not None and last_roll.is_success and uses_stress_track(before.target):
            state = append_event(after.state, f"{actor_id} rattles {target_id}.")
    elif ctx.action.id == "trip":
        if last_roll is None or not last_roll.is_success:
            state = append_event(after.state, f"{actor_id} fails to topple {target_id}.")
        else:
            state = append_event(after.state, f"{actor_id} puts {target_id} on the ground.")
    elif ctx.action.id == "feint":
        if last_roll is None or not last_roll.is_success:
            state = append_event(after.state, f"{actor_id} fails to topple {target_id}.")
        else:
            state = append_event(after.state, f"{actor_id} feints against {target_id}.")
    elif ctx.action.id == "shove":
        if last_roll is None or not last_roll.is_success:
            state = append_event(after.state, f"{actor_id} fails to shove {target_id}.")
        else:
            state = append_event(after.state, f"{actor_id} shoves {target_id} to {after.target.area_id}.")
    elif ctx.action.id == "stand_up":
        state = append_event(after.state, f"{actor_id} stands up.")
    return state


def _resolve_procedure(ctx: ActionResolutionContext) -> EncounterState:
    procedure = ctx.action.procedure
    assert procedure is not None
    before = ProcedureResolution.build(ctx)
    resolution = before
    for step in procedure.steps:
        if isinstance(step, AttackRollStep):
            resolution = _run_attack_step(ctx, resolution, step)
        elif isinstance(step, CheckRollStep):
            resolution = _run_check_step(ctx, resolution, step)
        elif isinstance(step, ContestRollStep):
            resolution = _run_contest_step(ctx, resolution, step)
        elif isinstance(step, ApplyConditionStep):
            resolution = _run_apply_condition_step(resolution, step)
        elif isinstance(step, ApplyHealingStep):
            resolution = _run_heal_step(ctx, resolution, step)
        elif isinstance(step, ApplyStressStep):
            resolution = _run_stress_step(ctx, resolution, step)
        elif isinstance(step, ApplyAttackModifierStep):
            resolution = _run_attack_modifier_step(ctx, resolution, step)
        elif isinstance(step, ClearConditionStep):
            resolution = _run_clear_condition_step(resolution, step)
        else:
            resolution = _run_move_target_step(ctx, resolution, step)
    return _finalize_procedure_action(ctx, before, resolution)


def apply_action_effect(
    state: EncounterState,
    actor: ActorState,
    target: ActorState,
    action: ActionDefinition,
    roller: DiceRoller,
    ruleset: Ruleset,
    push: bool,
    destination_area: str | None,
) -> EncounterState:
    ctx = ActionResolutionContext.build(
        state=state,
        actor=actor,
        target=target,
        action=action,
        roller=roller,
        ruleset=ruleset,
        push=push,
        destination_area=destination_area,
    )
    state = _resolve_procedure(ctx)
    if push:
        state = run_stress_test(state, state.actor(actor.actor_id), roller, ruleset)
    return state
