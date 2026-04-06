from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.actions import legal_actions_for_actor
from dead_by_dawn_sim.rules import load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner
from dead_by_dawn_sim.state import RangeBand, update_actor


def test_melee_actor_must_advance_when_not_engaged() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("single_pc_vs_slasher", seed=1)
    slasher_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_b"))
    slasher = state.actor(slasher_id)
    state = update_actor(state, replace(slasher, range_band=RangeBand.FAR))
    legal = legal_actions_for_actor(state, slasher_id, ruleset)
    action_ids = {action.action_id for action in legal}
    assert "advance" in action_ids
    assert "brawl_attack" not in action_ids
