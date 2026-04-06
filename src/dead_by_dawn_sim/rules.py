from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypeVar, cast

import yaml
from pydantic import BaseModel, Field


class DifficultyRules(BaseModel):
    challenging: int
    formidable: int


class PushRules(BaseModel):
    extra_die: int = 1
    keep: int = 2


class StressRules(BaseModel):
    starting: int
    panic_threshold: int
    breakdown_threshold: int


class DeathRules(BaseModel):
    wounded_to_critical_difficulty: Literal["challenging", "formidable"]
    critical_stabilize_difficulty: Literal["challenging", "formidable"]
    shrouds_to_die: int


class CoreRules(BaseModel):
    version: str
    check_dice: int
    save_dice: int
    keep_dice: int
    hp_base: int
    defense_base: int
    crit_on_doubles: bool
    difficulties: DifficultyRules
    push: PushRules
    stress: StressRules
    death: DeathRules
    max_rounds: int = 10


class AttackEffect(BaseModel):
    type: Literal["attack"]
    uses_weapon: bool = True
    stat: Literal["might", "speed", "wits"]
    skill: str


class HealEffect(BaseModel):
    type: Literal["heal"]
    amount: int
    difficulty: Literal["challenging", "formidable"]
    stat: Literal["might", "speed", "wits"]
    skill: str
    target: Literal["self", "ally"]


class StressEffect(BaseModel):
    type: Literal["stress"]
    amount: int
    difficulty: Literal["challenging", "formidable"]
    stat: Literal["might", "speed", "wits"]
    skill: str
    target: Literal["enemy"]


class DebuffAttackEffect(BaseModel):
    type: Literal["debuff_attack"]
    amount: int
    duration_rounds: int
    difficulty: Literal["challenging", "formidable"]
    stat: Literal["might", "speed", "wits"]
    skill: str
    target: Literal["enemy"]


ActionEffect = AttackEffect | HealEffect | StressEffect | DebuffAttackEffect


class ActionDefinition(BaseModel):
    id: str
    name: str
    action_cost: int
    tags: list[str]
    range: Literal["engaged", "near", "far", "self", "ally", "enemy"]
    allow_push: bool
    effect: ActionEffect = Field(discriminator="type")


class ConditionDefinition(BaseModel):
    id: str
    name: str
    tags: list[str]
    attack_modifier: int = 0
    damage_per_turn: int = 0


class WeaponDefinition(BaseModel):
    id: str
    name: str
    skill: str
    damage_die: int
    tags: list[str]
    max_range: Literal["engaged", "near", "far"]


class TalentEffect(BaseModel):
    type: Literal["final_girl", "healing_hands"]


class TalentDefinition(BaseModel):
    id: str
    name: str
    tags: list[str]
    effect: TalentEffect


class ActorTemplate(BaseModel):
    id: str
    name: str
    role: str
    default_persona: str
    stats: dict[Literal["might", "speed", "wits"], int]
    skills: dict[str, int]
    actions: list[str]
    weapon_id: str | None = None
    talents: list[str] = Field(default_factory=list)
    starting_band: Literal["engaged", "near", "far"] = "near"


class ScenarioSideEntry(BaseModel):
    template_id: str
    persona_id: str | None = None
    count: int = 1


class ScenarioDefinition(BaseModel):
    id: str
    name: str
    description: str
    team_a: list[ScenarioSideEntry]
    team_b: list[ScenarioSideEntry]


class BenchmarkSuite(BaseModel):
    id: str
    name: str
    scenario_ids: list[str]


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
        identifier = cast(str, model.model_dump()["id"])
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
    )
    validate_ruleset(ruleset)
    return ruleset


def validate_ruleset(ruleset: Ruleset) -> None:
    for actor in ruleset.actors.values():
        for action_id in actor.actions:
            if action_id not in ruleset.actions:
                raise ValueError(f"Actor {actor.id} references unknown action {action_id}.")
        if actor.weapon_id is not None and actor.weapon_id not in ruleset.weapons:
            raise ValueError(f"Actor {actor.id} references unknown weapon {actor.weapon_id}.")
        for talent_id in actor.talents:
            if talent_id not in ruleset.talents:
                raise ValueError(f"Actor {actor.id} references unknown talent {talent_id}.")
    for scenario in ruleset.scenarios.values():
        for side in [scenario.team_a, scenario.team_b]:
            for entry in side:
                if entry.template_id not in ruleset.actors:
                    msg = (
                        f"Scenario {scenario.id} references unknown actor template "
                        f"{entry.template_id}."
                    )
                    raise ValueError(msg)
    for suite in ruleset.benchmark_suites.values():
        for scenario_id in suite.scenario_ids:
            if scenario_id not in ruleset.scenarios:
                msg = f"Benchmark suite {suite.id} references unknown scenario {scenario_id}."
                raise ValueError(msg)


def count_ruleset_entities(ruleset: Ruleset) -> dict[str, int]:
    return {
        "actions": len(ruleset.actions),
        "actors": len(ruleset.actors),
        "benchmark_suites": len(ruleset.benchmark_suites),
        "conditions": len(ruleset.conditions),
        "scenarios": len(ruleset.scenarios),
        "talents": len(ruleset.talents),
        "weapons": len(ruleset.weapons),
    }
