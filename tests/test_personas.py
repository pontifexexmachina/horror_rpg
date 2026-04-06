from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.actions import legal_actions_for_actor
from dead_by_dawn_sim.personas import PERSONA_REGISTRY
from dead_by_dawn_sim.rules import load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner


def test_personas_make_different_choices_in_same_state() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("two_pc_vs_controller", seed=3)
    medic_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a_medic"))
    ally_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a_survivor"))
    state = replace(
        state,
        actors={
            **state.actors,
            ally_id: replace(state.actor(ally_id), hp=2),
        },
    )
    legal = legal_actions_for_actor(state, medic_id, ruleset)
    tactician_choice = PERSONA_REGISTRY["tactician"].choose_action(legal, state, ruleset)
    butt_kicker_choice = PERSONA_REGISTRY["butt_kicker"].choose_action(legal, state, ruleset)
    assert tactician_choice.action_id == "first_aid"
    assert butt_kicker_choice.action_id == "attack"
