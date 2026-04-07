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
from dead_by_dawn_sim.engine_state import apply_damage, remove_condition
from dead_by_dawn_sim.rules import (
    ActionDefinition,
    AttackRollStep,
    CheckRollStep,
    ContestRollStep,
    Ruleset,
    WeaponDefinition,
    action_has_heal_steps,
)
from dead_by_dawn_sim.state import (
    ActorState,
    ConditionState,
    EncounterState,
    TalentState,
    area_has_tag,
    update_actor,
)

RANGED_SKILLS = {"shoot"}


def _effective_attack_modifier(actor: ActorState, ruleset: Ruleset) -> int:
    modifier = 0
    for condition in actor.conditions:
        modifier += ruleset.conditions[condition.id].attack_modifier
    return modifier


def spend_attack_resource(actor: ActorState, effect: AttackRollStep, ruleset: Ruleset) -> ActorState:
    weapon = attack_weapon(effect, actor, ruleset)
    if weapon is None or weapon.ammo_kind is None:
        return actor
    current = actor.ammo.get(weapon.ammo_kind, 0)
    if current <= 0:
        raise ValueError(f"Actor {actor.actor_id} attempted a ranged attack without ammo.")
    next_ammo = dict(actor.ammo)
    next_ammo[weapon.ammo_kind] = current - 1
    return replace(actor, ammo=next_ammo)


def spend_bandage(actor: ActorState) -> ActorState:
    if actor.bandages <= 0:
        raise ValueError(f"Actor {actor.actor_id} attempted first aid without bandages.")
    return replace(actor, bandages=actor.bandages - 1)


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
    modifier += _effective_attack_modifier(actor, ruleset)
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


def auto_critical_heal_result(ctx: ActionResolutionContext, actor: ActorState) -> tuple[EncounterState, ActorState, RollResult]:
    updated_actor = replace(
        actor,
        talent_state=TalentState(used=actor.talent_state.used | {"healing_hands"}),
    )
    state = update_actor(ctx.state, updated_actor)
    result = RollResult(kept=[6, 6], total=999, is_success=True, is_critical=True)
    return state, updated_actor, result


def run_check_step(ctx: ActionResolutionContext, resolution: ProcedureResolution, step: CheckRollStep) -> ProcedureResolution:
    actor = resolution.actor
    state = resolution.state
    if ctx.action.id == "first_aid":
        actor = spend_bandage(actor)
        state = update_actor(state, actor)
    if action_has_heal_steps(ctx.action) and "healing_hands" in actor.talent_ids and "healing_hands" not in actor.talent_state.used:
        state, actor, result = auto_critical_heal_result(ctx, actor)
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
    actor = spend_attack_resource(resolution.actor, step, ctx.ruleset) if step.skill == "shoot" else resolution.actor
    state = update_actor(resolution.state, actor)
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
