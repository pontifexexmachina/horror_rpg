from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.actions import legal_actions_for_actor
from dead_by_dawn_sim.scripted_policies import POLICY_REGISTRY
from dead_by_dawn_sim.state import ActorStatus, synchronize_engagements
from tests.test_helpers import actor_id_with_prefix, build_state


def _casual_state_with_lone_terror(*, mover: tuple[str, str] | None = None):
    ruleset, state = build_state("casual_four_vs_triplet", seed=1)
    terror_id = actor_id_with_prefix(state, "team_b_terror")
    actor_updates = {
        actor_id: replace(actor, status=ActorStatus.DEAD, hp=0)
        for actor_id, actor in state.actors.items()
        if actor_id.startswith("team_b_") and actor_id != terror_id
    }
    if mover is not None:
        actor_id, area_id = mover
        actor_updates[actor_id] = replace(state.actor(actor_id), area_id=area_id)
        actor_updates[terror_id] = replace(state.actor(terror_id), area_id=area_id)
    state = replace(state, actors={**state.actors, **actor_updates})
    return ruleset, terror_id, synchronize_engagements(state)


def test_personas_make_different_choices_in_same_state() -> None:
    ruleset, state = build_state("two_pc_vs_controller", seed=3)
    medic_id = actor_id_with_prefix(state, "team_a_medic")
    ally_id = actor_id_with_prefix(state, "team_a_survivor")
    state = replace(
        state,
        actors={
            **state.actors,
            ally_id: replace(state.actor(ally_id), hp=2),
        },
    )
    legal = legal_actions_for_actor(state, medic_id, ruleset)
    tactician_choice = POLICY_REGISTRY["tactician"].choose_action(legal, state, ruleset)
    butt_kicker_choice = POLICY_REGISTRY["butt_kicker"].choose_action(legal, state, ruleset)
    assert tactician_choice.action_id == "first_aid"
    assert butt_kicker_choice.action_id == "attack"


def test_bruiser_advances_instead_of_gritting_at_full_hp() -> None:
    ruleset, state = build_state("hallway_ambush", seed=1)
    bruiser_id = actor_id_with_prefix(state, "team_a_bruiser")
    legal = legal_actions_for_actor(state, bruiser_id, ruleset)
    choice = POLICY_REGISTRY["butt_kicker"].choose_action(legal, state, ruleset)
    assert choice.action_id == "advance"
    assert choice.destination_area == "hallway"


def test_runner_policy_moves_toward_exit_when_escape_is_objective() -> None:
    ruleset, state = build_state("ballroom_escape", seed=1)
    survivor_id = actor_id_with_prefix(state, "team_a_survivor")
    legal = legal_actions_for_actor(state, survivor_id, ruleset)
    choice = POLICY_REGISTRY["power_gamer"].choose_action(legal, state, ruleset)
    assert choice.action_id == "advance"
    assert choice.destination_area == "ballroom"


def test_monster_policy_moves_to_intercept_exit_route() -> None:
    ruleset, state = build_state("ballroom_escape", seed=1)
    terror_id = actor_id_with_prefix(state, "team_b_terror")
    legal = legal_actions_for_actor(state, terror_id, ruleset)
    choice = POLICY_REGISTRY["panic_engine"].choose_action(legal, state, ruleset)
    assert choice.action_id == "advance"
    assert choice.destination_area == "ballroom"


def test_power_gamer_chases_last_enemy_instead_of_self_rallying() -> None:
    ruleset, state = build_state("hallway_ambush", seed=1)
    survivor_id = actor_id_with_prefix(state, "team_a_survivor")
    bruiser_id = actor_id_with_prefix(state, "team_a_bruiser")
    slasher_id = actor_id_with_prefix(state, "team_b_slasher")
    controller_id = actor_id_with_prefix(state, "team_b_controller")
    state = replace(
        state,
        actors={
            **state.actors,
            survivor_id: replace(state.actor(survivor_id), resources={**state.actor(survivor_id).resources, "sidearm": 0}),
            bruiser_id: replace(state.actor(bruiser_id), area_id="hallway"),
            slasher_id: replace(state.actor(slasher_id), status=ActorStatus.DEAD, hp=0),
            controller_id: replace(state.actor(controller_id), area_id="parlor"),
        },
    )
    state = synchronize_engagements(state)
    legal = legal_actions_for_actor(state, survivor_id, ruleset)
    choice = POLICY_REGISTRY["power_gamer"].choose_action(legal, state, ruleset)
    assert choice.action_id == "advance"
    assert choice.destination_area == "hallway"


def test_casual_bruiser_attacks_lone_enemy_instead_of_tripping() -> None:
    ruleset, state = build_state("casual_four_vs_triplet", seed=1)
    bruiser_id = actor_id_with_prefix(state, "team_a_bruiser")
    ruleset, _, state = _casual_state_with_lone_terror(mover=(bruiser_id, "arena"))
    legal = legal_actions_for_actor(state, bruiser_id, ruleset)
    choice = POLICY_REGISTRY["casual"].choose_action(legal, state, ruleset)
    assert choice.action_id == "brawl_attack"


def test_casual_medic_attacks_lone_enemy_instead_of_rallying_healthy_ally() -> None:
    ruleset, state = build_state("casual_four_vs_triplet", seed=1)
    medic_id = actor_id_with_prefix(state, "team_a_medic")
    ruleset, terror_id, state = _casual_state_with_lone_terror()
    legal = legal_actions_for_actor(state, medic_id, ruleset)
    choice = POLICY_REGISTRY["casual"].choose_action(legal, state, ruleset)
    assert choice.action_id == "attack"
    assert choice.target_id == terror_id


def test_tactician_attacks_low_hp_enemy_instead_of_tripping() -> None:
    ruleset, state = build_state("two_pc_vs_controller", seed=1)
    medic_id = actor_id_with_prefix(state, "team_a_medic")
    controller_id = actor_id_with_prefix(state, "team_b_controller")
    state = replace(
        state,
        actors={
            **state.actors,
            controller_id: replace(state.actor(controller_id), hp=2),
        },
    )
    state = synchronize_engagements(state)
    legal = legal_actions_for_actor(state, medic_id, ruleset)
    choice = POLICY_REGISTRY["tactician"].choose_action(legal, state, ruleset)
    assert choice.action_id == "attack"
    assert choice.target_id == controller_id

