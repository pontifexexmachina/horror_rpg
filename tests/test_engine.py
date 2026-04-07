from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.dice import FixedDiceRoller
from dead_by_dawn_sim.engine import determine_winner, resolve_action, resolve_roll
from dead_by_dawn_sim.rules import load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner
from dead_by_dawn_sim.state import (
    ActorStatus,
    EncounterState,
    synchronize_engagements,
    update_actor,
)


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
        scenario_id=state.scenario_id,
        objective=state.objective,
        areas=state.areas,
        connections=state.connections,
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


def test_ranged_attack_spends_ammo() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("single_pc_vs_slasher", seed=2)
    actor_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a"))
    target_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_b"))
    before = state.actor(actor_id).ammo["sidearm"]
    roller = FixedDiceRoller([6, 6, 4])
    result = resolve_action(
        state,
        ActionChoice(actor_id=actor_id, action_id="attack", target_id=target_id, push=False),
        roller,
        ruleset,
    )
    assert result.actor(actor_id).ammo["sidearm"] == before - 1


def test_cover_rich_area_increases_ranged_defense() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("hallway_ambush", seed=2)
    survivor_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_survivor")
    )
    controller_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_b_controller")
    )
    moved_state = synchronize_engagements(
        update_actor(state, replace(state.actor(survivor_id), area_id="hallway"))
    )
    roller = FixedDiceRoller([3, 2])
    result = resolve_action(
        moved_state,
        ActionChoice(actor_id=survivor_id, action_id="attack", target_id=controller_id, push=False),
        roller,
        ruleset,
    )
    assert result.actor(controller_id).hp == moved_state.actor(controller_id).hp


def test_dark_area_applies_ranged_concealment_penalty() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("hallway_ambush", seed=2)
    survivor_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_survivor")
    )
    slasher_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_b_slasher")
    )
    roller = FixedDiceRoller([3, 2])
    result = resolve_action(
        state,
        ActionChoice(actor_id=survivor_id, action_id="attack", target_id=slasher_id, push=False),
        roller,
        ruleset,
    )
    assert result.actor(slasher_id).hp == state.actor(slasher_id).hp


def test_monster_with_die_at_zero_dies_immediately() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("single_pc_vs_slasher", seed=2)
    actor_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a"))
    target_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_b"))
    target = state.actor(target_id)
    state = update_actor(state, replace(target, hp=1))
    roller = FixedDiceRoller([6, 6, 4])
    result = resolve_action(
        state,
        ActionChoice(actor_id=actor_id, action_id="attack", target_id=target_id, push=False),
        roller,
        ruleset,
    )
    assert result.actor(target_id).status is ActorStatus.DEAD


def test_first_aid_spends_bandage() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("two_pc_vs_brute", seed=2)
    medic_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a_medic"))
    ally_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a_survivor"))
    medic = state.actor(medic_id)
    injured_ally = replace(state.actor(ally_id), hp=3)
    state = EncounterState(
        scenario_id=state.scenario_id,
        objective=state.objective,
        areas=state.areas,
        connections=state.connections,
        actors={**state.actors, ally_id: injured_ally},
        round_number=state.round_number,
        initiative_order=state.initiative_order,
        active_actor_id=state.active_actor_id,
        winner=state.winner,
        events=state.events,
    )
    roller = FixedDiceRoller([6, 6])
    result = resolve_action(
        state,
        ActionChoice(actor_id=medic_id, action_id="first_aid", target_id=ally_id, push=False),
        roller,
        ruleset,
    )
    assert result.actor(medic_id).bandages == medic.bandages - 1


def test_grit_steadies_a_wounded_actor_without_healing() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("four_pc_vs_slasher", seed=2)
    bruiser_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser")
    )
    bruiser = state.actor(bruiser_id)
    state = EncounterState(
        scenario_id=state.scenario_id,
        objective=state.objective,
        areas=state.areas,
        connections=state.connections,
        actors={
            **state.actors,
            bruiser_id: replace(bruiser, hp=0, status=ActorStatus.WOUNDED),
        },
        round_number=state.round_number,
        initiative_order=state.initiative_order,
        active_actor_id=state.active_actor_id,
        winner=state.winner,
        events=state.events,
    )
    state = synchronize_engagements(state)
    roller = FixedDiceRoller([6, 6])
    result = resolve_action(
        state,
        ActionChoice(actor_id=bruiser_id, action_id="grit", target_id=bruiser_id, push=False),
        roller,
        ruleset,
    )
    updated_bruiser = result.actor(bruiser_id)
    assert updated_bruiser.hp == 0
    assert updated_bruiser.status is ActorStatus.WOUNDED
    assert any(condition.id == "steadied" for condition in updated_bruiser.conditions)


def test_movement_changes_area_and_updates_engagements() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("hallway_ambush", seed=2)
    bruiser_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser")
    )
    roller = FixedDiceRoller([6])
    result = resolve_action(
        state,
        ActionChoice(
            actor_id=bruiser_id,
            action_id="advance",
            target_id=bruiser_id,
            destination_area="hallway",
        ),
        roller,
        ruleset,
    )
    bruiser = result.actor(bruiser_id)
    assert bruiser.area_id == "hallway"
    assert any(target_id.startswith("team_b_slasher") for target_id in bruiser.engaged_with)


def test_reach_exit_objective_awards_team_a_win() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("ballroom_escape", seed=2)
    moved_actors = {
        actor_id: replace(actor, area_id="side_exit") if actor.team == "team_a" else actor
        for actor_id, actor in state.actors.items()
    }
    escaped_state = synchronize_engagements(
        EncounterState(
            scenario_id=state.scenario_id,
            objective=state.objective,
            areas=state.areas,
            connections=state.connections,
            actors=moved_actors,
            round_number=state.round_number,
            initiative_order=state.initiative_order,
            active_actor_id=state.active_actor_id,
            winner=state.winner,
            events=state.events,
        )
    )
    assert determine_winner(escaped_state) == "team_a"
