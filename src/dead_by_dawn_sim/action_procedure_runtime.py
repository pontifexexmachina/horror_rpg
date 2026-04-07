from __future__ import annotations

from dead_by_dawn_sim.action_procedure_rolls import (
    apply_attack_hit,
    attack_modifier_and_difficulty,
    roll_mode_for_action,
    run_attack_step,
    run_check_step,
    run_contest_step,
)
from dead_by_dawn_sim.action_procedure_steps import (
    finalize_procedure_action,
    run_apply_condition_step,
    run_attack_modifier_step,
    run_clear_condition_step,
    run_heal_step,
    run_move_target_step,
    run_stress_step,
)
from dead_by_dawn_sim.action_procedure_types import ActionResolutionContext, ProcedureResolution
from dead_by_dawn_sim.dice import DiceRoller
from dead_by_dawn_sim.engine_state import run_stress_test
from dead_by_dawn_sim.rules import (
    ActionDefinition,
    ApplyAttackModifierStep,
    ApplyConditionStep,
    ApplyHealingStep,
    ApplyStressStep,
    AttackRollStep,
    CheckRollStep,
    ClearConditionStep,
    ContestRollStep,
    Ruleset,
)
from dead_by_dawn_sim.state import ActorState, EncounterState


def _resolve_procedure(ctx: ActionResolutionContext) -> EncounterState:
    before = ProcedureResolution.build(ctx)
    resolution = before
    for step in ctx.action.procedure.steps:
        if isinstance(step, AttackRollStep):
            resolution = run_attack_step(ctx, resolution, step)
        elif isinstance(step, CheckRollStep):
            resolution = run_check_step(ctx, resolution, step)
        elif isinstance(step, ContestRollStep):
            resolution = run_contest_step(ctx, resolution, step)
        elif isinstance(step, ApplyConditionStep):
            resolution = run_apply_condition_step(resolution, step)
        elif isinstance(step, ApplyHealingStep):
            resolution = run_heal_step(ctx, resolution, step)
        elif isinstance(step, ApplyStressStep):
            resolution = run_stress_step(ctx, resolution, step)
        elif isinstance(step, ApplyAttackModifierStep):
            resolution = run_attack_modifier_step(ctx, resolution, step)
        elif isinstance(step, ClearConditionStep):
            resolution = run_clear_condition_step(resolution, step)
        else:
            resolution = run_move_target_step(ctx, resolution, step)
    return finalize_procedure_action(ctx, before, resolution)


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
    ctx = ActionResolutionContext(
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
    state = _resolve_procedure(ctx)
    if push:
        state = run_stress_test(state, state.actor(actor.actor_id), roller, ruleset)
    return state


__all__ = [
    "ActionResolutionContext",
    "ProcedureResolution",
    "apply_action_effect",
    "apply_attack_hit",
    "attack_modifier_and_difficulty",
    "roll_mode_for_action",
]
