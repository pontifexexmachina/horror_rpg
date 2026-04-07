from __future__ import annotations

from dataclasses import replace

import pytest
from pydantic import ValidationError

from dead_by_dawn_sim.rules import (
    ActionDefinition,
    ScenarioDefinition,
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
    assert counts["actions"] >= 7
    assert counts["session_plans"] >= 1
    assert counts["benchmark_suites"] >= 2
    assert "single_pc_vs_slasher" in ruleset.scenarios
    assert "hallway_ambush" in ruleset.scenarios
    assert "ballroom_escape" in ruleset.scenarios
    assert "spatial" in ruleset.benchmark_suites
    assert "core_night" in ruleset.session_plans
    assert "inspired" in ruleset.conditions
    assert "rally" in ruleset.actions
    assert ruleset.core.stress.panic_threshold == 8
    assert ruleset.core.stress.breakdown_threshold == 13
    assert ruleset.core.death.wounded_to_critical_difficulty == "formidable"
    assert ruleset.core.death.critical_stabilize_difficulty == "challenging"
    assert ruleset.core.death.shrouds_to_die == 3
    assert ruleset.weapons["pistol"].ammo_kind == "sidearm"
    assert ruleset.actors["medic"].starting_bandages == 3
    assert ruleset.actors["medic"].starting_medkits == 2
    assert ruleset.actors["slasher"].death_mode == "die_at_zero"
    assert ruleset.actors["slasher"].stress_mode == "ignore"
    assert ruleset.actors["controller"].death_mode == "die_at_zero"
    assert ruleset.actors["survivor"].death_mode == "pc_track"
    assert ruleset.actors["survivor"].stress_mode == "track"
    assert ruleset.scenarios["single_pc_vs_slasher"].areas[0].id == "arena"
    assert ruleset.scenarios["hallway_ambush"].objective.type == "defeat_enemies"
    assert ruleset.scenarios["ballroom_escape"].objective.type == "reach_exit"


def test_unknown_effect_type_is_rejected() -> None:
    payload = {
        "id": "bad_action",
        "name": "Bad Action",
        "action_cost": 1,
        "tags": ["attack"],
        "range": "enemy",
        "allow_push": False,
        "effect": {
            "type": "unknown",
        },
    }
    with pytest.raises(ValidationError):
        ActionDefinition.model_validate(payload)


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
