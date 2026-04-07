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
    ActionEffect,
    AttackEffect,
    BuffEffect,
    ContestConditionEffect,
    ContestDebuffEffect,
    ContestMoveEffect,
    DebuffAttackEffect,
    HealEffect,
    RemoveConditionEffect,
    Ruleset,
    StressEffect,
    WeaponDefinition,
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
    effect: ActionEffect
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
        effect = action.effect
        return cls(
            state=state,
            actor=actor,
            target=target,
            action=action,
            effect=effect,
            roller=roller,
            ruleset=ruleset,
            push=push,
            destination_area=destination_area,
            roll_mode=roll_mode_for_action(actor, target, effect),
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
    actor: ActorState,
    target: ActorState,
    effect: ActionEffect,
) -> RollMode:
    swing = 0
    if isinstance(effect, AttackEffect):
        if has_condition(actor, "inspired") or has_condition(actor, "feinting"):
            swing += 1
        if has_condition(target, "prone"):
            swing += 1
    if getattr(effect, "target", None) == "enemy":
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


def _resolve_skill_effect_result(
    effect: BuffEffect | StressEffect | DebuffAttackEffect,
    *,
    actor: ActorState,
    roller: DiceRoller,
    ruleset: Ruleset,
    push: bool,
    roll_mode: RollMode,
) -> RollResult:
    return _resolve_effect_check(
        actor=actor,
        stat=effect.stat,
        skill=effect.skill,
        difficulty_name=effect.difficulty,
        roller=roller,
        ruleset=ruleset,
        push=push,
        roll_mode=roll_mode,
    )


def _resolve_contest_effect_result(
    effect: ContestDebuffEffect | ContestConditionEffect | ContestMoveEffect,
    *,
    actor: ActorState,
    target: ActorState,
    roller: DiceRoller,
    ruleset: Ruleset,
    push: bool,
    roll_mode: RollMode,
) -> ContestResult:
    return _resolve_effect_contest(
        actor=actor,
        target=target,
        stat=effect.stat,
        skill=effect.skill,
        defense_stat=effect.defense_stat,
        roller=roller,
        ruleset=ruleset,
        push=push,
        roll_mode=roll_mode,
    )


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


def _apply_condition_result(
    state: EncounterState,
    *,
    actor: ActorState,
    target: ActorState,
    result: RollResult | ContestResult,
    duration_rounds: int,
) -> EncounterState:
    if not result.is_success:
        return state
    return _apply_rattled(state, actor=actor, target=target, duration_rounds=duration_rounds)


def _handle_attack_effect(ctx: ActionResolutionContext, effect: AttackEffect) -> EncounterState:
    weapon = attack_weapon(effect, ctx.actor, ctx.ruleset)
    if weapon is None:
        raise ValueError(f"Actor {ctx.actor.actor_id} attempted an attack without a weapon.")
    actor = (
        _spend_attack_resource(ctx.actor, effect, ctx.ruleset)
        if effect.skill == "shoot"
        else ctx.actor
    )
    state = update_actor(ctx.state, actor)
    modifier, difficulty = attack_modifier_and_difficulty(
        state, actor, ctx.target, effect, ctx.ruleset
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
        return apply_attack_hit(
            state,
            target=ctx.target,
            weapon=weapon,
            roller=ctx.roller,
            ruleset=ctx.ruleset,
            critical=result.is_critical,
            event=f"{ctx.actor.actor_id} hits {ctx.target.actor_id} for {{damage}}.",
        )
    return append_event(state, f"{ctx.actor.actor_id} misses {ctx.target.actor_id}.")


def _resolve_heal_result(
    ctx: ActionResolutionContext, effect: HealEffect
) -> tuple[EncounterState, ActorState, RollResult]:
    actor = ctx.actor
    state = ctx.state
    if ctx.action.id == "first_aid":
        actor = _spend_bandage(actor)
        state = update_actor(state, actor)
    modifier = actor.stats[effect.stat] + actor.skills.get(effect.skill, 0)
    if "healing_hands" in actor.talent_ids and "healing_hands" not in actor.talent_state.used:
        result = RollResult(kept=[6, 6], total=999, is_success=True, is_critical=True)
        actor = replace(
            actor,
            talent_state=TalentState(used=actor.talent_state.used | {"healing_hands"}),
        )
        state = update_actor(state, actor)
        return state, actor, result
    result = roll_check(
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        modifier=modifier,
        difficulty=difficulty_value(ctx.ruleset, effect.difficulty),
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    return state, actor, result


def _handle_heal_effect(ctx: ActionResolutionContext, effect: HealEffect) -> EncounterState:
    state, actor, result = _resolve_heal_result(ctx, effect)
    if not result.is_success:
        return append_event(state, f"{actor.actor_id} fails to heal {ctx.target.actor_id}.")
    amount = effect.amount + (1 if result.is_critical else 0)
    updated_target = heal_target(ctx.target, amount, ctx.ruleset)
    if ctx.action.id == "grit":
        updated_target = remove_condition(updated_target, "bleeding")
    state = update_actor(state, updated_target)
    return append_event(state, f"{actor.actor_id} heals {ctx.target.actor_id} for {amount}.")


def _handle_buff_effect(ctx: ActionResolutionContext, effect: BuffEffect) -> EncounterState:
    result = _resolve_skill_effect_result(
        effect,
        actor=ctx.actor,
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    if not result.is_success:
        return append_event(
            ctx.state, f"{ctx.actor.actor_id} fails to rally {ctx.target.actor_id}."
        )
    updated_target = replace(
        ctx.target,
        conditions=(
            *ctx.target.conditions,
            ConditionState(id=effect.condition_id, rounds_remaining=effect.duration_rounds),
        ),
    )
    if result.is_critical and effect.crit_heal_amount > 0:
        updated_target = heal_target(updated_target, effect.crit_heal_amount, ctx.ruleset)
    state = update_actor(ctx.state, updated_target)
    return append_event(state, f"{ctx.actor.actor_id} rallies {ctx.target.actor_id}.")


def _handle_stress_effect(ctx: ActionResolutionContext, effect: StressEffect) -> EncounterState:
    result = _resolve_skill_effect_result(
        effect,
        actor=ctx.actor,
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    if not result.is_success or not uses_stress_track(ctx.target):
        return ctx.state
    updated_target = transition_actor_state(
        replace(ctx.target, stress=ctx.target.stress + effect.amount), ctx.ruleset
    )
    state = update_actor(ctx.state, updated_target)
    return append_event(state, f"{ctx.actor.actor_id} rattles {ctx.target.actor_id}.")


def _handle_debuff_attack_effect(
    ctx: ActionResolutionContext, effect: DebuffAttackEffect
) -> EncounterState:
    result = _resolve_skill_effect_result(
        effect,
        actor=ctx.actor,
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    return _apply_condition_result(
        ctx.state,
        actor=ctx.actor,
        target=ctx.target,
        result=result,
        duration_rounds=effect.duration_rounds,
    )


def _handle_contest_debuff_effect(
    ctx: ActionResolutionContext, effect: ContestDebuffEffect
) -> EncounterState:
    result = _resolve_contest_effect_result(
        effect,
        actor=ctx.actor,
        target=ctx.target,
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    return _apply_condition_result(
        ctx.state,
        actor=ctx.actor,
        target=ctx.target,
        result=result,
        duration_rounds=effect.duration_rounds,
    )


def _handle_remove_condition_effect(
    ctx: ActionResolutionContext, effect: RemoveConditionEffect
) -> EncounterState:
    updated_actor = remove_condition(ctx.actor, effect.condition_id)
    state = update_actor(ctx.state, updated_actor)
    return append_event(state, f"{ctx.actor.actor_id} stands up.")


def _handle_contest_condition_effect(
    ctx: ActionResolutionContext, effect: ContestConditionEffect
) -> EncounterState:
    result = _resolve_contest_effect_result(
        effect,
        actor=ctx.actor,
        target=ctx.target,
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    if not result.is_success:
        return append_event(
            ctx.state, f"{ctx.actor.actor_id} fails to topple {ctx.target.actor_id}."
        )
    recipient = ctx.actor if effect.apply_to == "self" else ctx.target
    updated_recipient = _append_condition(
        recipient,
        effect.condition_id,
        effect.duration_rounds,
    )
    state = update_actor(ctx.state, updated_recipient)
    if effect.apply_to == "self":
        return append_event(state, f"{ctx.actor.actor_id} feints against {ctx.target.actor_id}.")
    return append_event(state, f"{ctx.actor.actor_id} puts {ctx.target.actor_id} on the ground.")


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


def _handle_contest_move_effect(
    ctx: ActionResolutionContext, effect: ContestMoveEffect
) -> EncounterState:
    destination_area = _validate_move_destination(ctx)
    result = _resolve_contest_effect_result(
        effect,
        actor=ctx.actor,
        target=ctx.target,
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    if not result.is_success:
        return append_event(
            ctx.state, f"{ctx.actor.actor_id} fails to shove {ctx.target.actor_id}."
        )
    state = _move_target(ctx.state, ctx.target, destination_area)
    moved_target = state.actor(ctx.target.actor_id)
    if result.is_critical and effect.crit_condition_id is not None:
        moved_target = replace(
            moved_target,
            conditions=(
                *moved_target.conditions,
                ConditionState(
                    id=effect.crit_condition_id,
                    rounds_remaining=effect.crit_duration_rounds,
                ),
            ),
        )
        state = update_actor(state, moved_target)
    return append_event(
        state, f"{ctx.actor.actor_id} shoves {ctx.target.actor_id} to {destination_area}."
    )


def _resolve_effect(ctx: ActionResolutionContext) -> EncounterState:
    effect = ctx.effect
    state: EncounterState
    if isinstance(effect, AttackEffect):
        state = _handle_attack_effect(ctx, effect)
    elif isinstance(effect, HealEffect):
        state = _handle_heal_effect(ctx, effect)
    elif isinstance(effect, BuffEffect):
        state = _handle_buff_effect(ctx, effect)
    elif isinstance(effect, StressEffect):
        state = _handle_stress_effect(ctx, effect)
    elif isinstance(effect, DebuffAttackEffect):
        state = _handle_debuff_attack_effect(ctx, effect)
    elif isinstance(effect, ContestDebuffEffect):
        state = _handle_contest_debuff_effect(ctx, effect)
    elif isinstance(effect, RemoveConditionEffect):
        state = _handle_remove_condition_effect(ctx, effect)
    elif isinstance(effect, ContestConditionEffect):
        state = _handle_contest_condition_effect(ctx, effect)
    else:
        state = _handle_contest_move_effect(ctx, effect)
    return state


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
    state = _resolve_effect(ctx)
    if push:
        state = run_stress_test(state, state.actor(actor.actor_id), roller, ruleset)
    return state
