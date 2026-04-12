from __future__ import annotations

from pathlib import Path

import yaml


def test_scripted_policies_yaml_exists_and_has_expected_policies() -> None:
    path = Path("data/policies/scripted.yml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert path.exists()
    assert isinstance(raw, dict)
    assert set(raw) == {
        "power_gamer",
        "butt_kicker",
        "tactician",
        "method_actor",
        "casual",
        "brute",
        "controller",
        "panic_engine",
        "finisher",
    }
    assert raw["tactician"]["push_threshold"] == 0.8