from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel

from dead_by_dawn_sim.rules_action_models import ActionDefinition
from dead_by_dawn_sim.rules_content_models import (
    ActorTemplate,
    BenchmarkSuite,
    ConditionDefinition,
    CoreRules,
    ScenarioDefinition,
    SessionPlan,
    TalentDefinition,
    WeaponDefinition,
)


@dataclass(frozen=True)
class Ruleset:
    core: CoreRules
    actions: dict[str, ActionDefinition]
    conditions: dict[str, ConditionDefinition]
    weapons: dict[str, WeaponDefinition]
    talents: dict[str, TalentDefinition]
    actors: dict[str, ActorTemplate]
    scenarios: dict[str, ScenarioDefinition]
    benchmark_suites: dict[str, BenchmarkSuite]
    session_plans: dict[str, SessionPlan]

    @property
    def version(self) -> str:
        return self.core.version


TModel = TypeVar("TModel", bound=BaseModel)


def _load_yaml(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_map(directory: Path, model_type: type[TModel]) -> dict[str, TModel]:
    loaded: dict[str, TModel] = {}
    for path in sorted(directory.glob("*.yml")):
        raw = _load_yaml(path)
        if not isinstance(raw, dict):
            msg = f"{path} must contain a mapping at the top level."
            raise ValueError(msg)
        model = model_type.model_validate(raw)
        identifier = getattr(model, "id", None)
        if not isinstance(identifier, str):
            raise ValueError(f"{path} must define a string id field.")
        if identifier in loaded:
            raise ValueError(f"{directory} defines duplicate id {identifier}.")
        loaded[identifier] = model
    return loaded


def load_ruleset(data_dir: str | Path = "data") -> Ruleset:
    base = Path(data_dir)
    core = CoreRules.model_validate(_load_yaml(base / "core_rules" / "default.yml"))
    ruleset = Ruleset(
        core=core,
        actions=_load_map(base / "actions", ActionDefinition),
        conditions=_load_map(base / "conditions", ConditionDefinition),
        weapons=_load_map(base / "weapons", WeaponDefinition),
        talents=_load_map(base / "talents", TalentDefinition),
        actors=_load_map(base / "actors", ActorTemplate),
        scenarios=_load_map(base / "scenarios", ScenarioDefinition),
        benchmark_suites=_load_map(base / "benchmark_suites", BenchmarkSuite),
        session_plans=_load_map(base / "session_plans", SessionPlan),
    )
    validate_ruleset(ruleset)
    return ruleset


def validate_ruleset(ruleset: Ruleset) -> None:
    from dead_by_dawn_sim.rules_validation import validate_ruleset as _validate_ruleset

    _validate_ruleset(ruleset)


def count_ruleset_entities(ruleset: Ruleset) -> dict[str, int]:
    return {
        "actions": len(ruleset.actions),
        "actors": len(ruleset.actors),
        "benchmark_suites": len(ruleset.benchmark_suites),
        "conditions": len(ruleset.conditions),
        "scenarios": len(ruleset.scenarios),
        "session_plans": len(ruleset.session_plans),
        "talents": len(ruleset.talents),
        "weapons": len(ruleset.weapons),
    }
