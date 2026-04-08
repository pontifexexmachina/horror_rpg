from __future__ import annotations

from dataclasses import replace
from typing import Literal

from dead_by_dawn_sim.action_procedure_narration import narrate_attack_hit, narrate_attack_miss
from dead_by_dawn_sim.action_procedure_types import ActionResolutionContext, ProcedureResolution
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
    mark_talent_effect_used,
    remove_condition,
    talent_effect_for_actor,
    talent_effect_used,
)
from dead_by_dawn_sim.rules import (
    ActionDefinition,
    AttackRollStep,
    CheckRollStep,
    ContestRollStep,
    Ruleset,
    SpendAmmoStep,
    SpendResourceStep,
    TalentEffect,
    WeaponDefinition,
    action_has_heal_steps,
)
from dead_by_dawn_sim.state import (
    ActorState,
    ConditionState,
    EncounterState,
    area_has_tag,
    update_actor,
)

RANGED_SKILLS = {"shoot"}


def _effective_attack_modifier(
    actor: ActorState, target: ActorState, ruleset: Ruleset
) -> int:
    modifier = 0
    for condition in actor.conditions:
        modifier += ruleset.conditions[condition.id].attack_modifier
    for attack_modifier in actor.attack_modifiers:
        if (
            attack_modifier.source_actor_id is None
            or attack_modifier.source_actor_id == target.actor_id
        ):
            modifier += attack_modifier.amount
    return modifier


def spend_attack_ammo(actor: ActorState, effect: AttackRollStep, ruleset: Ruleset, amount: int) -> ActorState:
    weapon = attack_weapon(effect, actor, ruleset)
    if weapon is None or weapon.ammo_kind is None:
        return actor
    current = actor.ammo.get(weapon.ammo_kind, 0)
    if current < amount:
        raise ValueError(f"Actor {actor.actor_id} attempted a ranged attack without enough ammo.")
    next_resources = dict(actor.resources)
    next_resources[weapon.ammo_kind] = current - amount
    return replace(actor, resources=next_resources)


def spend_resource(actor: ActorState, resource: str, amount: int) -> ActorState:
    current = actor.resource_amount(resource)
    if current < amount:
        raise ValueError(
            f"Actor {actor.actor_id} attempted to spend {amount} {resource} with only {current}."
        )
    next_resources = dict(actor.resources)
    next_resources[resource] = current - amount
    return replace(actor, resources=next_resources)


def roll_mode_for_action(action: ActionDefinition, actor: ActorState, target: ActorState) -> RollMode:
    swing = 0
    if any(isinstance(step, AttackRollStep) for step in action.procedure.steps):
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


def consume_attack_conditions(actor: ActorState) -> ActorState:
    actor = remove_condition(actor, "inspired")
    return remove_condition(actor, "feinting")


def attack_modifier_and_difficulty(state: EncounterState, actor: ActorState, target: ActorState, effect: AttackRollStep, ruleset: Ruleset) -> tuple[int, int]:
    modifier = actor.stats[effect.stat] + actor.skills.get(effect.skill, 0)
    modifier += _effective_attack_modifier(actor, target, ruleset)
    difficulty = target.defense
    if effect.skill in RANGED_SKILLS:
        if actor.area_id != target.area_id and area_has_tag(state, target.area_id, "dark"):
            modifier -= 1
        if actor.area_id != target.area_id and area_has_tag(state, target.area_id, "cover_rich"):
            difficulty += 1
    return modifier, difficulty


def _effect_modifier(actor: ActorState, stat: Literal["might", "speed", "wits"], skill: str) -> int:
    return actor.stats[stat] + actor.skills.get(skill, 0)


def resolve_effect_check(
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


def resolve_effect_contest(
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


def append_condition(target: ActorState, condition_id: str, rounds_remaining: int, *, source_actor_id: str | None = None) -> ActorState:
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


def apply_attack_hit(state: EncounterState, *, target: ActorState, weapon: WeaponDefinition, roller: DiceRoller, ruleset: Ruleset, critical: bool, event: str) -> EncounterState:
    damage_roll = roller.roll_d6(1)[0]
    damage = weapon.damage_die if critical else min(damage_roll, weapon.damage_die)
    updated_target = apply_damage(target, damage, ruleset)
    if "bleed" in weapon.tags:
        updated_target = append_condition(updated_target, "bleeding", 3)
    state = update_actor(state, updated_target)
    return narrate_attack_hit(state, event.format(damage=damage))


def auto_critical_heal_result(
    ctx: ActionResolutionContext, actor: ActorState, effect: TalentEffect
) -> tuple[EncounterState, ActorState, RollResult]:
    updated_actor = mark_talent_effect_used(actor, effect)
    state = update_actor(ctx.state, updated_actor)
    result = RollResult(kept=[6, 6], total=999, is_success=True, is_critical=True)
    return state, updated_actor, result


def run_check_step(ctx: ActionResolutionContext, resolution: ProcedureResolution, step: CheckRollStep) -> ProcedureResolution:
    actor = resolution.actor
    state = resolution.state
    healing_effect = talent_effect_for_actor(actor, ctx.ruleset, "auto_critical_heal")
    if (
        action_has_heal_steps(ctx.action)
        and healing_effect is not None
        and not talent_effect_used(actor, healing_effect)
    ):
        state, actor, result = auto_critical_heal_result(ctx, actor, healing_effect)
        return resolution.with_state(state, actor_id=actor.actor_id, target_id=resolution.target.actor_id, last_roll=result)
    result = resolve_effect_check(
        actor=actor,
        stat=step.stat,
        skill=step.skill,
        difficulty_name=step.difficulty,
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    return resolution.with_state(state, actor_id=actor.actor_id, target_id=resolution.target.actor_id, last_roll=result)


def run_contest_step(ctx: ActionResolutionContext, resolution: ProcedureResolution, step: ContestRollStep) -> ProcedureResolution:
    result = resolve_effect_contest(
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
    return resolution.with_state(resolution.state, actor_id=resolution.actor.actor_id, target_id=resolution.target.actor_id, last_roll=result)


def run_attack_step(ctx: ActionResolutionContext, resolution: ProcedureResolution, step: AttackRollStep) -> ProcedureResolution:
    weapon = attack_weapon(step, resolution.actor, ctx.ruleset)
    if weapon is None:
        raise ValueError(f"Actor {resolution.actor.actor_id} attempted an attack without a weapon.")
    actor = resolution.actor
    state = resolution.state
    modifier, difficulty = attack_modifier_and_difficulty(state, actor, resolution.target, step, ctx.ruleset)
    result = roll_check(
        roller=ctx.roller,
        ruleset=ctx.ruleset,
        modifier=modifier,
        difficulty=difficulty,
        push=ctx.push,
        roll_mode=ctx.roll_mode,
    )
    actor_after = consume_attack_conditions(state.actor(actor.actor_id))
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
        state = narrate_attack_miss(state, resolution.actor.actor_id, resolution.target.actor_id)
    return resolution.with_state(state, actor_id=resolution.actor.actor_id, target_id=resolution.target.actor_id, last_roll=result)



def run_spend_resource_step(
    ctx: ActionResolutionContext, resolution: ProcedureResolution, step: SpendResourceStep
) -> ProcedureResolution:
    if step.when != "always" and resolution.last_roll is not None:
        if step.when == "success" and not resolution.last_roll.is_success:
            return resolution
        if step.when == "critical" and not resolution.last_roll.is_critical:
            return resolution
    actor = spend_resource(resolution.actor, step.resource, step.amount)
    state = update_actor(resolution.state, actor)
    return resolution.with_state(
        state,
        actor_id=actor.actor_id,
        target_id=resolution.target.actor_id,
    )


def run_spend_ammo_step(
    ctx: ActionResolutionContext, resolution: ProcedureResolution, step: SpendAmmoStep
) -> ProcedureResolution:
    if step.when != "always" and resolution.last_roll is not None:
        if step.when == "success" and not resolution.last_roll.is_success:
            return resolution
        if step.when == "critical" and not resolution.last_roll.is_critical:
            return resolution
    attack_step = next(
        (procedure_step for procedure_step in ctx.action.procedure.steps if isinstance(procedure_step, AttackRollStep)),
        None,
    )
    if attack_step is None:
        raise ValueError(f"Action {ctx.action.id} cannot spend ammo without an attack step.")
    actor = spend_attack_ammo(resolution.actor, attack_step, ctx.ruleset, step.amount)
    state = update_actor(resolution.state, actor)
    return resolution.with_state(
        state,
        actor_id=actor.actor_id,
        target_id=resolution.target.actor_id,
    )
