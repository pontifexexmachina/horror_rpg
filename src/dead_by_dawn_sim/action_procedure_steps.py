from __future__ import annotations

from dataclasses import replace
from typing import Literal

from dead_by_dawn_sim.action_procedure_narration import (
    narrate_procedure_action,
    narrate_rattled_aim,
)
from dead_by_dawn_sim.action_procedure_rolls import append_condition
from dead_by_dawn_sim.action_procedure_types import ActionResolutionContext, ProcedureResolution
from dead_by_dawn_sim.engine_rolls import ContestResult, RollResult
from dead_by_dawn_sim.engine_state import (
    heal_target,
    remove_condition,
    transition_actor_state,
    uses_stress_track,
)
from dead_by_dawn_sim.rules import (
    ApplyAttackModifierStep,
    ApplyConditionStep,
    ApplyHealingStep,
    ApplyStressStep,
    ClearConditionStep,
    MoveTargetStep,
)
from dead_by_dawn_sim.state import (
    ActorState,
    EncounterState,
    can_enter_area,
    connected_area_ids,
    synchronize_engagements,
    update_actor,
)


def procedure_recipient(resolution: ProcedureResolution, target_name: str) -> ActorState:
    if target_name == "self":
        return resolution.actor
    return resolution.target


def procedure_result_applies(last_roll: RollResult | ContestResult | None, when: Literal["always", "success", "critical"]) -> bool:
    if when == "always":
        return True
    if last_roll is None or not last_roll.is_success:
        return False
    if when == "success":
        return True
    return last_roll.is_critical


def apply_rattled(
    state: EncounterState,
    *,
    actor: ActorState,
    target: ActorState,
    duration_rounds: int,
) -> EncounterState:
    updated_target = append_condition(target, "rattled", duration_rounds, source_actor_id=actor.actor_id)
    state = update_actor(state, updated_target)
    return narrate_rattled_aim(state, actor.actor_id, target.actor_id)


def move_target(state: EncounterState, target: ActorState, destination_area: str) -> EncounterState:
    moved = update_actor(state, replace(target, area_id=destination_area, engaged_with=frozenset()))
    return synchronize_engagements(moved)


def validate_move_destination(ctx: ActionResolutionContext) -> str:
    if ctx.destination_area is None:
        raise ValueError(f"Action {ctx.action.id} requires a destination area.")
    if ctx.destination_area not in connected_area_ids(ctx.state, ctx.target.area_id):
        raise ValueError(f"Action {ctx.action.id} cannot move {ctx.target.actor_id} to {ctx.destination_area}.")
    if not can_enter_area(ctx.state, ctx.destination_area):
        raise ValueError(f"Action {ctx.action.id} cannot move {ctx.target.actor_id} into a full area.")
    return ctx.destination_area


def run_apply_condition_step(resolution: ProcedureResolution, step: ApplyConditionStep) -> ProcedureResolution:
    if not procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    recipient = procedure_recipient(resolution, step.target)
    updated = append_condition(recipient, step.condition_id, step.duration_rounds)
    state = update_actor(resolution.state, updated)
    return resolution.with_state(state, actor_id=resolution.actor.actor_id, target_id=resolution.target.actor_id)


def run_heal_step(ctx: ActionResolutionContext, resolution: ProcedureResolution, step: ApplyHealingStep) -> ProcedureResolution:
    if not procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    recipient = procedure_recipient(resolution, step.target)
    updated = heal_target(recipient, step.amount, ctx.ruleset)
    state = update_actor(resolution.state, updated)
    return resolution.with_state(state, actor_id=resolution.actor.actor_id, target_id=resolution.target.actor_id)


def run_stress_step(ctx: ActionResolutionContext, resolution: ProcedureResolution, step: ApplyStressStep) -> ProcedureResolution:
    if not procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    recipient = procedure_recipient(resolution, step.target)
    if not uses_stress_track(recipient):
        return resolution
    updated = transition_actor_state(replace(recipient, stress=recipient.stress + step.amount), ctx.ruleset)
    state = update_actor(resolution.state, updated)
    return resolution.with_state(state, actor_id=resolution.actor.actor_id, target_id=resolution.target.actor_id)


def run_attack_modifier_step(ctx: ActionResolutionContext, resolution: ProcedureResolution, step: ApplyAttackModifierStep) -> ProcedureResolution:
    if not procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    if step.target != "target":
        raise ValueError("Attack modifier procedure steps currently only support target recipients.")
    state = apply_rattled(resolution.state, actor=resolution.actor, target=resolution.target, duration_rounds=step.duration_rounds)
    return resolution.with_state(state, actor_id=resolution.actor.actor_id, target_id=resolution.target.actor_id)


def run_clear_condition_step(resolution: ProcedureResolution, step: ClearConditionStep) -> ProcedureResolution:
    if not procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    recipient = procedure_recipient(resolution, step.target)
    updated = remove_condition(recipient, step.condition_id)
    state = update_actor(resolution.state, updated)
    return resolution.with_state(state, actor_id=resolution.actor.actor_id, target_id=resolution.target.actor_id)


def run_move_target_step(ctx: ActionResolutionContext, resolution: ProcedureResolution, step: MoveTargetStep) -> ProcedureResolution:
    if not procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    if step.destination != "choice":
        raise ValueError(f"Unsupported move destination mode {step.destination}.")
    destination_area = validate_move_destination(ctx)
    state = move_target(resolution.state, resolution.target, destination_area)
    return resolution.with_state(state, actor_id=resolution.actor.actor_id, target_id=resolution.target.actor_id)


def finalize_procedure_action(
    ctx: ActionResolutionContext,
    before: ProcedureResolution,
    after: ProcedureResolution,
) -> EncounterState:
    return narrate_procedure_action(ctx, before, after, uses_stress_track(before.target))
