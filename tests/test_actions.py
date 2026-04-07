from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.actions import legal_actions_for_actor
from dead_by_dawn_sim.rules import ConnectionDefinition, load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner
from dead_by_dawn_sim.state import EncounterState, synchronize_engagements, update_actor


def test_melee_actor_gets_movement_options_when_enemy_is_one_area_away() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("hallway_ambush", seed=1)
    bruiser_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser")
    )
    legal = legal_actions_for_actor(state, bruiser_id, ruleset)
    movement = [choice for choice in legal if choice.action_id == "advance"]
    assert movement
    assert {choice.destination_area for choice in movement} == {"hallway"}
    assert "brawl_attack" not in {choice.action_id for choice in legal}


def test_out_of_ammo_removes_ranged_attack_but_keeps_fallback_melee() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("single_pc_vs_slasher", seed=1)
    survivor_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a"))
    survivor = state.actor(survivor_id)
    state = update_actor(state, replace(survivor, ammo={"sidearm": 0}))
    legal = legal_actions_for_actor(state, survivor_id, ruleset)
    action_ids = {action.action_id for action in legal}
    assert "attack" not in action_ids
    assert "brawl_attack" in action_ids


def test_first_aid_requires_bandages() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("two_pc_vs_brute", seed=1)
    medic_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a_medic"))
    medic = state.actor(medic_id)
    state = update_actor(state, replace(medic, bandages=0))
    legal = legal_actions_for_actor(state, medic_id, ruleset)
    action_ids = {action.action_id for action in legal}
    assert "first_aid" not in action_ids


def test_grit_is_not_available_to_healthy_actor() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("four_pc_vs_slasher", seed=1)
    bruiser_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser")
    )
    legal = legal_actions_for_actor(state, bruiser_id, ruleset)
    assert "grit" not in {action.action_id for action in legal}


def test_rally_targets_adjacent_allies_in_same_area() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("two_pc_vs_controller", seed=1)
    medic_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a_medic"))
    legal = legal_actions_for_actor(state, medic_id, ruleset)
    rally_targets = {choice.target_id for choice in legal if choice.action_id == "rally"}
    assert any(target_id.startswith("team_a_survivor") for target_id in rally_targets)
    assert not any(target_id.startswith("team_b") for target_id in rally_targets)


def test_ranged_attacks_can_reach_connected_areas_but_not_two_hops() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("ballroom_escape", seed=1)
    survivor_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_survivor")
    )
    legal = legal_actions_for_actor(state, survivor_id, ruleset)
    shoot_targets = {choice.target_id for choice in legal if choice.action_id == "attack"}
    assert any(target_id.startswith("team_b_slasher") for target_id in shoot_targets)
    assert not any(target_id.startswith("team_b_terror") for target_id in shoot_targets)


def test_blocked_sight_connection_prevents_cross_area_shots() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("ballroom_escape", seed=1)
    opaque_state = EncounterState(
        scenario_id=state.scenario_id,
        objective=state.objective,
        areas=state.areas,
        connections=(
            ConnectionDefinition(
                id="gallery_to_ballroom",
                from_area="gallery",
                to_area="ballroom",
                tags=["blocked_sight"],
                bidirectional=True,
            ),
            *state.connections[1:],
        ),
        actors=state.actors,
        round_number=state.round_number,
        initiative_order=state.initiative_order,
        active_actor_id=state.active_actor_id,
        used_reactions=state.used_reactions,
        winner=state.winner,
        events=state.events,
    )
    survivor_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_survivor")
    )
    legal = legal_actions_for_actor(opaque_state, survivor_id, ruleset)
    shoot_targets = {choice.target_id for choice in legal if choice.action_id == "attack"}
    assert not any(target_id.startswith("team_b_slasher") for target_id in shoot_targets)


def test_cramped_area_prevents_extra_body_from_entering() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("hallway_ambush", seed=1)
    survivor_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_survivor")
    )
    bruiser_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser")
    )
    moved_state = synchronize_engagements(
        update_actor(state, replace(state.actor(bruiser_id), area_id="hallway"))
    )
    legal = legal_actions_for_actor(moved_state, survivor_id, ruleset)
    movement = [choice for choice in legal if choice.action_id == "advance"]
    assert all(choice.destination_area != "hallway" for choice in movement)


def test_grit_is_available_when_injured() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("four_pc_vs_slasher", seed=1)
    bruiser_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser")
    )
    bruiser = state.actor(bruiser_id)
    state = update_actor(state, replace(bruiser, hp=bruiser.max_hp - 2))
    legal = legal_actions_for_actor(state, bruiser_id, ruleset)
    assert "grit" in {action.action_id for action in legal}
