from __future__ import annotations

import pytest
from pydantic import ValidationError

from dead_by_dawn_sim.rules import ActionDefinition, count_ruleset_entities, load_ruleset


def test_load_ruleset_from_repo_data() -> None:
    ruleset = load_ruleset()
    counts = count_ruleset_entities(ruleset)
    assert ruleset.version == "0.1.0"
    assert counts["actions"] >= 5
    assert "single_pc_vs_slasher" in ruleset.scenarios


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
