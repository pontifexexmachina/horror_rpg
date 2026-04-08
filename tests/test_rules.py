from __future__ import annotations

from dataclasses import replace

import pytest
from pydantic import ValidationError

from dead_by_dawn_sim.rules import (
    ActionDefinition,
    AmmoAtLeastRequirement,
    ApplyAttackModifierStep,
    ApplyConditionStep,
    ApplyHealingStep,
    AttackRollStep,
    CheckRollStep,
    ClearConditionStep,
    ContestRollStep,
    InterludeTreatmentRule,
    MoveTargetStep,
    ScenarioDefinition,
    SpendAmmoStep,
    SpendResourceStep,
    count_ruleset_entities,
    load_ruleset,
    validate_ruleset,
)


def _assert_invalid_scenario(data: dict[str, object], match: str) -> None:
    ruleset = load_ruleset()
    invalid = ScenarioDefinition.model_validate(data)
    broken_ruleset = replace(
        ruleset,
        scenarios={**ruleset.scenarios, invalid.id: invalid},
    )
    with pytest.raises(ValueError, match=match):
        validate_ruleset(broken_ruleset)


def test_load_ruleset_from_repo_data() -> None:
    ruleset = load_ruleset()
    counts = count_ruleset_entities(ruleset)
    assert ruleset.version == "0.1.0"
    assert counts["actions"] >= 9
    assert counts["session_plans"] >= 1
    assert counts["benchmark_suites"] >= 2
    assert "single_pc_vs_slasher" in ruleset.scenarios
    assert "hallway_ambush" in ruleset.scenarios
    assert "ballroom_escape" in ruleset.scenarios
    assert "spatial" in ruleset.benchmark_suites
    assert "core_night" in ruleset.session_plans
    assert isinstance(ruleset.session_plans["core_night"].interlude.treatments[0], InterludeTreatmentRule)
    assert ruleset.session_plans["core_night"].interlude.treatments[0].resource == "medkits"
    assert ruleset.session_plans["core_night"].interlude.treatments[0].heal_amount == 2
    assert "inspired" in ruleset.conditions
    assert "rally" in ruleset.actions
    assert "advance" in ruleset.actions
    assert "fall_back" in ruleset.actions
    assert ruleset.core.stress.panic_threshold == 8
    assert ruleset.core.stress.breakdown_threshold == 13
    assert ruleset.core.death.wounded_to_critical_difficulty == "formidable"
    assert ruleset.core.death.critical_stabilize_difficulty == "challenging"
    assert ruleset.core.death.shrouds_to_die == 3
    assert ruleset.weapons["pistol"].ammo_kind == "sidearm"
    assert ruleset.actors["medic"].starting_resources.get("bandages", 0) == 3
    assert ruleset.actors["medic"].starting_resources.get("medkits", 0) == 2
    assert ruleset.actors["slasher"].death_mode == "die_at_zero"
    assert ruleset.actors["slasher"].stress_mode == "ignore"
    assert ruleset.actors["controller"].death_mode == "die_at_zero"
    assert ruleset.actors["survivor"].death_mode == "pc_track"
    assert ruleset.actors["survivor"].stress_mode == "track"
    assert ruleset.scenarios["single_pc_vs_slasher"].areas[0].id == "arena"
    assert ruleset.scenarios["hallway_ambush"].objective.type == "defeat_enemies"
    assert ruleset.scenarios["ballroom_escape"].objective.type == "reach_exit"


def test_missing_procedure_is_rejected() -> None:
    payload = {
        "id": "bad_action",
        "name": "Bad Action",
        "action_cost": 1,
        "tags": ["attack"],
        "range": "enemy",
        "allow_push": False,
    }
    with pytest.raises(ValidationError):
        ActionDefinition.model_validate(payload)


def test_actor_starting_resources_require_non_empty_keys() -> None:
    ruleset = load_ruleset()
    medic = ruleset.actors["medic"]
    with pytest.raises(ValidationError):
        type(medic).model_validate(
            {
                **medic.model_dump(),
                "starting_resources": {"": 1},
            }
        )


def test_validate_ruleset_rejects_unknown_start_area() -> None:
    _assert_invalid_scenario(
        {
            "id": "bad_start_area",
            "name": "Bad Start Area",
            "description": "Broken fixture.",
            "areas": [{"id": "foyer", "name": "Foyer"}],
            "team_a": [{"template_id": "survivor", "start_area": "nowhere"}],
            "team_b": [{"template_id": "slasher", "start_area": "foyer"}],
        },
        "unknown start area",
    )


def test_validate_ruleset_rejects_unknown_connection_endpoint() -> None:
    _assert_invalid_scenario(
        {
            "id": "bad_connection",
            "name": "Bad Connection",
            "description": "Broken fixture.",
            "areas": [{"id": "foyer", "name": "Foyer"}],
            "connections": [{"id": "foyer_to_void", "from_area": "foyer", "to_area": "void"}],
            "team_a": [{"template_id": "survivor", "start_area": "foyer"}],
            "team_b": [{"template_id": "slasher", "start_area": "foyer"}],
        },
        "unknown area endpoint",
    )


def test_actions_expose_declarative_procedures() -> None:
    ruleset = load_ruleset()

    rally_steps = ruleset.actions["rally"].procedure
    assert rally_steps is not None
    assert isinstance(rally_steps.steps[0], CheckRollStep)
    assert isinstance(rally_steps.steps[1], ApplyConditionStep)
    assert isinstance(rally_steps.steps[2], ApplyHealingStep)

    trip_steps = ruleset.actions["trip"].procedure
    assert trip_steps is not None
    assert isinstance(trip_steps.steps[0], ContestRollStep)
    assert isinstance(trip_steps.steps[1], ApplyConditionStep)

    shove_steps = ruleset.actions["shove"].procedure
    assert shove_steps is not None
    assert isinstance(shove_steps.steps[1], MoveTargetStep)

    attack = ruleset.actions["attack"]
    attack_steps = attack.procedure
    assert attack_steps is not None
    assert isinstance(attack.availability.all_of[0], AmmoAtLeastRequirement)
    assert isinstance(attack_steps.steps[0], SpendAmmoStep)
    assert isinstance(attack_steps.steps[1], AttackRollStep)

    first_aid_steps = ruleset.actions["first_aid"].procedure
    assert first_aid_steps is not None
    assert isinstance(first_aid_steps.steps[0], SpendResourceStep)
    assert isinstance(first_aid_steps.steps[1], CheckRollStep)

    stand_up_steps = ruleset.actions["stand_up"].procedure
    assert stand_up_steps is not None
    assert isinstance(stand_up_steps.steps[0], ClearConditionStep)

    taunt_steps = ruleset.actions["taunt"].procedure
    assert taunt_steps is not None
    assert isinstance(taunt_steps.steps[1], ApplyAttackModifierStep)
    assert isinstance(taunt_steps.steps[2], ApplyConditionStep)
