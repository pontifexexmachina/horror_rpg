"""Direct tests for internal implementation modules."""
from __future__ import annotations

import random
from dataclasses import replace as dc_replace

import pytest

from dead_by_dawn_sim.action_procedure_effects import append_condition
from dead_by_dawn_sim.action_procedure_narration import NARRATION_HANDLERS, narrate_procedure_action
from dead_by_dawn_sim.action_procedure_resources import run_spend_resource_step
from dead_by_dawn_sim.action_procedure_rolls import roll_mode_for_action, run_spend_ammo_step
from dead_by_dawn_sim.action_procedure_runtime import apply_action_effect
from dead_by_dawn_sim.action_procedure_steps import procedure_result_applies
from dead_by_dawn_sim.action_procedure_types import ActionResolutionContext, ProcedureResolution
from dead_by_dawn_sim.combat_support import attack_weapon
from dead_by_dawn_sim.dice import FixedDiceRoller, RandomDiceRoller
from dead_by_dawn_sim.engine_rolls import RollResult
from dead_by_dawn_sim.rules import load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner
from dead_by_dawn_sim.state import update_actor


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_ctx(ruleset=None, action_id="attack", push=False):
    if ruleset is None:
        ruleset = load_ruleset()
    state = EncounterRunner(ruleset).build_state("single_pc_vs_slasher", seed=1)
    actor_id = next(a for a in state.actors if a.startswith("team_a"))
    target_id = next(a for a in state.actors if a.startswith("team_b"))
    actor = state.actor(actor_id)
    target = state.actor(target_id)
    action = ruleset.actions[action_id]
    return ActionResolutionContext(
        state=state,
        actor=actor,
        target=target,
        action=action,
        roller=RandomDiceRoller(rng=random.Random(1)),
        ruleset=ruleset,
        push=push,
        destination_area=None,
        roll_mode=roll_mode_for_action(action, actor, target),
    )


# ---------------------------------------------------------------------------
# procedure_result_applies (action_procedure_steps)
# ---------------------------------------------------------------------------

def test_procedure_result_applies_always_returns_true_with_no_roll() -> None:
    assert procedure_result_applies(None, "always") is True


def test_procedure_result_applies_success_returns_false_with_no_roll() -> None:
    assert procedure_result_applies(None, "success") is False


def test_procedure_result_applies_critical_returns_false_with_no_roll() -> None:
    assert procedure_result_applies(None, "critical") is False


def test_procedure_result_applies_always_true_on_failure() -> None:
    roll = RollResult(kept=[1], total=1, is_success=False, is_critical=False)
    assert procedure_result_applies(roll, "always") is True


def test_procedure_result_applies_success_false_on_failure() -> None:
    roll = RollResult(kept=[1], total=1, is_success=False, is_critical=False)
    assert procedure_result_applies(roll, "success") is False


def test_procedure_result_applies_success_true_on_success() -> None:
    roll = RollResult(kept=[6], total=6, is_success=True, is_critical=False)
    assert procedure_result_applies(roll, "success") is True


def test_procedure_result_applies_critical_false_on_non_critical_success() -> None:
    roll = RollResult(kept=[6], total=6, is_success=True, is_critical=False)
    assert procedure_result_applies(roll, "critical") is False


def test_procedure_result_applies_critical_true_on_critical() -> None:
    roll = RollResult(kept=[6, 6], total=12, is_success=True, is_critical=True)
    assert procedure_result_applies(roll, "critical") is True


# ---------------------------------------------------------------------------
# dice
# ---------------------------------------------------------------------------

def test_random_dice_roller_returns_correct_count() -> None:
    roller = RandomDiceRoller(rng=random.Random(42))
    results = roller.roll_d6(count=3)
    assert len(results) == 3
    assert all(1 <= r <= 6 for r in results)


def test_random_dice_roller_is_deterministic() -> None:
    r1 = RandomDiceRoller(rng=random.Random(99))
    r2 = RandomDiceRoller(rng=random.Random(99))
    assert r1.roll_d6(5) == r2.roll_d6(5)


def test_fixed_dice_roller_returns_fixed_values() -> None:
    roller = FixedDiceRoller(values=[6, 3, 1])
    assert roller.roll_d6(2) == [6, 3]
    assert roller.roll_d6(1) == [1]


def test_fixed_dice_roller_raises_when_exhausted() -> None:
    roller = FixedDiceRoller(values=[6])
    with pytest.raises(ValueError, match="fixed values remain"):
        roller.roll_d6(5)


# ---------------------------------------------------------------------------
# combat_support
# ---------------------------------------------------------------------------

def test_attack_weapon_returns_weapon_for_actor_with_weapon_id() -> None:
    ruleset = load_ruleset()
    attack_action = ruleset.actions["attack"]
    attack_step = next(s for s in attack_action.procedure.steps if hasattr(s, "weapon_id"))
    state = EncounterRunner(ruleset).build_state("single_pc_vs_slasher", seed=1)
    actor_id = next(a for a in state.actors if a.startswith("team_b"))
    actor = state.actor(actor_id)
    weapon = attack_weapon(attack_step, actor, ruleset)
    assert weapon is not None


def test_attack_weapon_returns_none_when_no_weapon_id() -> None:
    ruleset = load_ruleset()
    attack_action = ruleset.actions["attack"]
    attack_step = next(s for s in attack_action.procedure.steps if hasattr(s, "weapon_id"))
    state = EncounterRunner(ruleset).build_state("single_pc_vs_slasher", seed=1)
    actor_id = next(a for a in state.actors if a.startswith("team_b"))
    actor = state.actor(actor_id)
    actor_no_weapon = dc_replace(actor, weapon_id=None)
    unarmed_step = attack_step.model_copy(update={"weapon_id": None})
    result = attack_weapon(unarmed_step, actor_no_weapon, ruleset)
    assert result is None


# ---------------------------------------------------------------------------
# action_procedure_types
# ---------------------------------------------------------------------------

def test_procedure_resolution_build_from_context() -> None:
    ctx = _make_ctx()
    resolution = ProcedureResolution.build(ctx)
    assert resolution.state is ctx.state
    assert resolution.actor.actor_id == ctx.actor.actor_id
    assert resolution.target.actor_id == ctx.target.actor_id
    assert resolution.last_roll is None


def test_action_resolution_context_with_state_refreshes_actors() -> None:
    ctx = _make_ctx()
    modified_actor = dc_replace(ctx.actor, hp=1)
    new_state = update_actor(ctx.state, modified_actor)
    new_ctx = ctx.with_state(new_state)
    assert new_ctx.actor.hp == 1
    assert new_ctx.state is new_state


# ---------------------------------------------------------------------------
# action_procedure_effects
# ---------------------------------------------------------------------------

def test_append_condition_adds_to_actor() -> None:
    ctx = _make_ctx()
    actor = ctx.actor
    updated = append_condition(actor, "bleeding", rounds_remaining=3)
    condition_ids = [c.id for c in updated.conditions]
    assert "bleeding" in condition_ids


def test_append_condition_preserves_existing_conditions() -> None:
    ctx = _make_ctx()
    actor = ctx.actor
    with_one = append_condition(actor, "prone", rounds_remaining=2)
    with_two = append_condition(with_one, "bleeding", rounds_remaining=3)
    condition_ids = [c.id for c in with_two.conditions]
    assert "prone" in condition_ids
    assert "bleeding" in condition_ids


def test_append_condition_records_source_actor() -> None:
    ctx = _make_ctx()
    updated = append_condition(ctx.target, "prone", rounds_remaining=1, source_actor_id=ctx.actor.actor_id)
    source_ids = [c.source_actor_id for c in updated.conditions]
    assert ctx.actor.actor_id in source_ids


# ---------------------------------------------------------------------------
# action_procedure_narration
# ---------------------------------------------------------------------------

def test_narration_handlers_covers_expected_action_types() -> None:
    expected = {"heal", "rally", "shriek", "trip", "feint", "shove", "stand_up"}
    assert expected.issubset(NARRATION_HANDLERS.keys())


def test_narrate_procedure_action_returns_state_unchanged_for_unknown_narration_id() -> None:
    ctx = _make_ctx(action_id="attack")
    resolution = ProcedureResolution.build(ctx)
    result = narrate_procedure_action(ctx, resolution, resolution, target_uses_stress_track=False)
    # "attack" has no narration_id → state returned unchanged (no extra events appended)
    assert result is resolution.state


# ---------------------------------------------------------------------------
# action_procedure_resources
# ---------------------------------------------------------------------------

def test_run_spend_resource_step_deducts_resource_on_always() -> None:
    from dead_by_dawn_sim.rules import SpendResourceStep
    ruleset = load_ruleset()
    state = EncounterRunner(ruleset).build_state("single_pc_vs_slasher", seed=1)
    actor_id = next(a for a in state.actors if a.startswith("team_a"))
    actor = state.actor(actor_id)
    # Give actor a bandage
    actor_with_bandage = dc_replace(actor, resources={**actor.resources, "bandages": 3})
    state = update_actor(state, actor_with_bandage)
    resolution = ProcedureResolution(state=state, actor=state.actor(actor_id), target=state.actor(actor_id))
    step = SpendResourceStep(type="spend_resource", resource="bandages", amount=1, when="always")
    result = run_spend_resource_step(resolution, step)
    assert result.actor.resources.get("bandages", 0) == 2


# ---------------------------------------------------------------------------
# action_procedure_runtime (apply_action_effect)
# ---------------------------------------------------------------------------

def test_apply_action_effect_returns_updated_state() -> None:
    ruleset = load_ruleset()
    state = EncounterRunner(ruleset).build_state("single_pc_vs_slasher", seed=1)
    actor_id = next(a for a in state.actors if a.startswith("team_b"))
    target_id = next(a for a in state.actors if a.startswith("team_a"))
    actor = state.actor(actor_id)
    target = state.actor(target_id)
    action = ruleset.actions["brawl_attack"]
    roller = FixedDiceRoller(values=[6, 6, 6, 6, 6, 6, 6, 6])
    result = apply_action_effect(
        state,
        actor,
        target,
        action,
        roller=roller,
        ruleset=ruleset,
        push=False,
        destination_area=None,
    )
    assert isinstance(result.events, tuple)


# ---------------------------------------------------------------------------
# narration (continued)
# ---------------------------------------------------------------------------

def test_narrate_procedure_action_appends_event_on_success() -> None:
    ruleset = load_ruleset()
    ctx = _make_ctx(ruleset=ruleset, action_id="rally")
    resolution = ProcedureResolution.build(ctx)
    success_roll = RollResult(kept=[6], total=6, is_success=True, is_critical=False)
    after = ProcedureResolution(
        state=resolution.state,
        actor=resolution.actor,
        target=resolution.target,
        last_roll=success_roll,
    )
    result = narrate_procedure_action(ctx, resolution, after, target_uses_stress_track=False)
    assert len(result.events) > len(resolution.state.events)
