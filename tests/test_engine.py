from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.dice import FixedDiceRoller
from dead_by_dawn_sim.engine import resolve_action, resolve_roll
from dead_by_dawn_sim.rules import load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner
from dead_by_dawn_sim.state import EncounterState


def test_resolve_roll_detects_critical_success() -> None:
    result = resolve_roll(raw_rolls=[6, 6], keep=2, modifier=0, difficulty=8)
    assert result.is_success is True
    assert result.is_critical is True


def test_push_attack_triggers_stress_test_and_can_gain_stress() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("single_pc_vs_slasher", seed=2)
    actor_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a"))
    target_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_b"))
    actor = state.actor(actor_id)
    state = EncounterState(
        actors={**state.actors, actor_id: replace(actor, stress=12)},
        round_number=state.round_number,
        initiative_order=state.initiative_order,
        active_actor_id=state.active_actor_id,
        winner=state.winner,
        events=state.events,
    )
    roller = FixedDiceRoller([6, 6, 3, 1, 1, 1, 1])
    result = resolve_action(
        state,
        ActionChoice(actor_id=actor_id, action_id="attack", target_id=target_id, push=True),
        roller,
        ruleset,
    )
    assert result.actor(actor_id).stress >= 13
