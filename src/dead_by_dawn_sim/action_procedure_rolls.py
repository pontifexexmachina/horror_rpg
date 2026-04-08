from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from dead_by_dawn_sim.action_procedure_effects import apply_attack_hit, auto_critical_heal_result
from dead_by_dawn_sim.action_procedure_resources import (
    run_spend_ammo_step as _run_spend_ammo_step,
)
from dead_by_dawn_sim.action_procedure_resources import (
    run_spend_resource_step as _run_spend_resource_step,
)
from dead_by_dawn_sim.combat_support import attack_weapon, has_condition
from dead_by_dawn_sim.engine_rolls import (
    ContestResult,
    RollMode,
    RollResult,
    difficulty_value,
    roll_check,
    roll_contest,
)
from dead_by_dawn_sim.engine_state import (
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
    action_has_heal_steps,
    attack_step_for_action,
)
from dead_by_dawn_sim.state import ActorState, EncounterState, append_event, area_has_tag, update_actor

if TYPE_CHECKING:
    from dead_by_dawn_sim.action_procedure_types import ActionResolutionContext, ProcedureResolution
    from dead_by_dawn_sim.dice import DiceRoller

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


def attack_modifier_and_difficulty(
    state: EncounterState,
    actor: ActorState,
    target: ActorState,
    effect: AttackRollStep,
    ruleset: Ruleset,
) -> tuple[int, int]:
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


def run_check_step(
    ctx: ActionResolutionContext, resolution: ProcedureResolution, step: CheckRollStep
) -> ProcedureResolution:
    actor = resolution.actor
    state = resolution.state
    healing_effect = talent_effect_for_actor(actor, ctx.ruleset, "auto_critical_heal")
    if (
        action_has_heal_steps(ctx.action)
        and healing_effect is not None
        and not talent_effect_used(actor, healing_effect)
    ):
        state, actor, result = auto_critical_heal_result(ctx, actor, healing_effect)
        return resolution.with_state(
            state,
            actor_id=actor.actor_id,
            target_id=resolution.target.actor_id,
            last_roll=result,
        )
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
    return resolution.with_state(
        state,
        actor_id=actor.actor_id,
        target_id=resolution.target.actor_id,
        last_roll=result,
    )


def run_contest_step(
    ctx: ActionResolutionContext, resolution: ProcedureResolution, step: ContestRollStep
) -> ProcedureResolution:
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
    return resolution.with_state(
        resolution.state,
        actor_id=resolution.actor.actor_id,
        target_id=resolution.target.actor_id,
        last_roll=result,
    )


def run_attack_step(
    ctx: ActionResolutionContext, resolution: ProcedureResolution, step: AttackRollStep
) -> ProcedureResolution:
    weapon = attack_weapon(step, resolution.actor, ctx.ruleset)
    if weapon is None:
        raise ValueError(f"Actor {resolution.actor.actor_id} attempted an attack without a weapon.")
    actor = resolution.actor
    state = resolution.state
    modifier, difficulty = attack_modifier_and_difficulty(
        state, actor, resolution.target, step, ctx.ruleset
    )
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
        state = append_event(state, f"{resolution.actor.actor_id} misses {resolution.target.actor_id}.")
    return resolution.with_state(
        state,
        actor_id=resolution.actor.actor_id,
        target_id=resolution.target.actor_id,
        last_roll=result,
    )


def run_spend_resource_step(
    _ctx: ActionResolutionContext, resolution: ProcedureResolution, step: SpendResourceStep
) -> ProcedureResolution:
    return _run_spend_resource_step(resolution, step)


def run_spend_ammo_step(
    ctx: ActionResolutionContext, resolution: ProcedureResolution, step: SpendAmmoStep
) -> ProcedureResolution:
    return _run_spend_ammo_step(resolution, attack_step_for_action(ctx.action), ctx.ruleset, step)
