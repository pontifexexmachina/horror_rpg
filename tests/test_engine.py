from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.dice import FixedDiceRoller
from dead_by_dawn_sim.engine import determine_winner, resolve_action, resolve_roll, start_turn
from dead_by_dawn_sim.rules import load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner
from dead_by_dawn_sim.state import (
    ActorStatus,
    ConditionState,
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
        used_reactions=state.used_reactions,
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
        used_reactions=state.used_reactions,
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


def test_grit_heals_and_clears_bleeding() -> None:
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
            bruiser_id: replace(
                bruiser,
                hp=4,
                conditions=(*bruiser.conditions, ConditionState(id="bleeding", rounds_remaining=3)),
            ),
        },
        round_number=state.round_number,
        initiative_order=state.initiative_order,
        active_actor_id=state.active_actor_id,
        used_reactions=state.used_reactions,
        winner=state.winner,
        events=state.events,
    )
    roller = FixedDiceRoller([6, 6])
    result = resolve_action(
        state,
        ActionChoice(actor_id=bruiser_id, action_id="grit", target_id=bruiser_id, push=False),
        roller,
        ruleset,
    )
    updated_bruiser = result.actor(bruiser_id)
    assert updated_bruiser.hp == 7
    assert not any(condition.id == "bleeding" for condition in updated_bruiser.conditions)


def test_taunt_condition_persists_into_target_turn() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("hallway_ambush", seed=2)
    occultist_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_b_controller")
    )
    target_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser"))
    taunted = resolve_action(
        state,
        ActionChoice(actor_id=occultist_id, action_id="taunt", target_id=target_id, push=False),
        FixedDiceRoller([6, 6]),
        ruleset,
    )
    started = start_turn(taunted, target_id, ruleset)
    assert any(condition.id == "rattled" for condition in started.actor(target_id).conditions)


def test_rally_applies_inspired_and_can_heal_on_crit() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("two_pc_vs_controller", seed=2)
    medic_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a_medic"))
    ally_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a_survivor"))
    state = update_actor(state, replace(state.actor(ally_id), hp=6))
    result = resolve_action(
        state,
        ActionChoice(actor_id=medic_id, action_id="rally", target_id=ally_id, push=False),
        FixedDiceRoller([6, 6]),
        ruleset,
    )
    rallied = result.actor(ally_id)
    assert rallied.hp == 7
    assert any(condition.id == "inspired" for condition in rallied.conditions)


def test_trip_applies_prone() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("hallway_ambush", seed=2)
    bruiser_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser")
    )
    slasher_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_b_slasher")
    )
    engaged_state = synchronize_engagements(
        update_actor(state, replace(state.actor(bruiser_id), area_id="hallway"))
    )
    result = resolve_action(
        engaged_state,
        ActionChoice(actor_id=bruiser_id, action_id="trip", target_id=slasher_id, push=False),
        FixedDiceRoller([6, 6, 1, 1]),
        ruleset,
    )
    assert any(condition.id == "prone" for condition in result.actor(slasher_id).conditions)


def test_shove_moves_target_and_knocks_prone_on_critical() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("hallway_ambush", seed=2)
    bruiser_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser")
    )
    slasher_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_b_slasher")
    )
    engaged_state = synchronize_engagements(
        update_actor(state, replace(state.actor(bruiser_id), area_id="hallway"))
    )
    result = resolve_action(
        engaged_state,
        ActionChoice(
            actor_id=bruiser_id,
            action_id="shove",
            target_id=slasher_id,
            destination_area="parlor",
            push=False,
        ),
        FixedDiceRoller([6, 6, 1, 1]),
        ruleset,
    )
    shoved = result.actor(slasher_id)
    assert shoved.area_id == "parlor"
    assert any(condition.id == "prone" for condition in shoved.conditions)


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


def test_fall_back_triggers_reaction_attack() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("hallway_ambush", seed=2)
    bruiser_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser")
    )
    slasher_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_b_slasher")
    )
    engaged_state = synchronize_engagements(
        update_actor(state, replace(state.actor(bruiser_id), area_id="hallway"))
    )
    starting_hp = engaged_state.actor(bruiser_id).hp
    result = resolve_action(
        engaged_state,
        ActionChoice(
            actor_id=bruiser_id,
            action_id="fall_back",
            target_id=bruiser_id,
            destination_area="entry",
        ),
        FixedDiceRoller([6, 6, 4]),
        ruleset,
    )
    assert result.actor(bruiser_id).area_id == "entry"
    assert result.actor(bruiser_id).hp == starting_hp - 6
    assert slasher_id in result.used_reactions


def test_reactor_can_only_make_one_reaction_per_round() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("hallway_ambush", seed=2)
    bruiser_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser")
    )
    survivor_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_survivor")
    )
    slasher_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_b_slasher")
    )
    staged_state = synchronize_engagements(
        update_actor(
            update_actor(state, replace(state.actor(bruiser_id), area_id="hallway")),
            replace(state.actor(survivor_id), area_id="hallway"),
        )
    )
    bruiser_hp = staged_state.actor(bruiser_id).hp
    survivor_hp = staged_state.actor(survivor_id).hp
    after_bruiser = resolve_action(
        staged_state,
        ActionChoice(
            actor_id=bruiser_id,
            action_id="fall_back",
            target_id=bruiser_id,
            destination_area="entry",
        ),
        FixedDiceRoller([6, 6, 4]),
        ruleset,
    )
    after_survivor = resolve_action(
        after_bruiser,
        ActionChoice(
            actor_id=survivor_id,
            action_id="fall_back",
            target_id=survivor_id,
            destination_area="entry",
        ),
        FixedDiceRoller([6, 6, 4]),
        ruleset,
    )
    assert slasher_id in after_survivor.used_reactions
    assert after_bruiser.actor(bruiser_id).hp == bruiser_hp - 6
    assert after_survivor.actor(survivor_id).hp == survivor_hp


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
            used_reactions=state.used_reactions,
            winner=state.winner,
            events=state.events,
        )
    )
    assert determine_winner(escaped_state) == "team_a"


def test_stress_attack_does_not_affect_monsters() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("casual_four_vs_triplet", seed=2)
    occultist_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_a_occultist")
    )
    terror_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_b_terror"))
    result = resolve_action(
        state,
        ActionChoice(actor_id=occultist_id, action_id="shriek", target_id=terror_id, push=False),
        FixedDiceRoller([6, 6]),
        ruleset,
    )
    assert result.actor(terror_id).stress == 0


def test_monsters_do_not_gain_stress_from_pushing() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    state = runner.build_state("hallway_ambush", seed=2)
    controller_id = next(
        actor_id for actor_id in state.actors if actor_id.startswith("team_b_controller")
    )
    target_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a_bruiser"))
    result = resolve_action(
        state,
        ActionChoice(actor_id=controller_id, action_id="taunt", target_id=target_id, push=True),
        FixedDiceRoller([6, 6, 1, 1]),
        ruleset,
    )
    assert result.actor(controller_id).stress == 0
