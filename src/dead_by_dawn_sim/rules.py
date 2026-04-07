from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal, TypeVar, cast

import yaml
from pydantic import BaseModel, Field, model_validator


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
    weapon_id: str | None = None
    stat: Literal["might", "speed", "wits"]
    skill: str


class HealEffect(BaseModel):
    type: Literal["heal"]
    amount: int
    difficulty: Literal["challenging", "formidable"]
    stat: Literal["might", "speed", "wits"]
    skill: str
    target: Literal["self", "ally"]


class BuffEffect(BaseModel):
    type: Literal["buff"]
    difficulty: Literal["challenging", "formidable"]
    stat: Literal["might", "speed", "wits"]
    skill: str
    target: Literal["ally", "self"]
    condition_id: str
    duration_rounds: int
    crit_heal_amount: int = 0


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


class ContestDebuffEffect(BaseModel):
    type: Literal["contest_debuff"]
    amount: int
    duration_rounds: int
    stat: Literal["might", "speed", "wits"]
    skill: str
    target: Literal["enemy"]
    defense_stat: Literal["might", "speed", "wits"]


class ContestConditionEffect(BaseModel):
    type: Literal["contest_condition"]
    stat: Literal["might", "speed", "wits"]
    skill: str
    target: Literal["enemy"]
    defense_stat: Literal["might", "speed", "wits"]
    condition_id: str
    duration_rounds: int
    apply_to: Literal["target", "self"] = "target"


class ContestMoveEffect(BaseModel):
    type: Literal["contest_move"]
    stat: Literal["might", "speed", "wits"]
    skill: str
    target: Literal["enemy"]
    defense_stat: Literal["might", "speed", "wits"]
    crit_condition_id: str | None = None
    crit_duration_rounds: int = 0


class RemoveConditionEffect(BaseModel):
    type: Literal["remove_condition"]
    target: Literal["self"]
    condition_id: str


ActionOutcome = Literal["always", "success", "critical"]
ProcedureTarget = Literal["self", "target"]
MoveDestination = Literal["choice"]


class AttackRollStep(BaseModel):
    type: Literal["attack"]
    uses_weapon: bool = True
    weapon_id: str | None = None
    stat: Literal["might", "speed", "wits"]
    skill: str


class CheckRollStep(BaseModel):
    type: Literal["check"]
    difficulty: Literal["challenging", "formidable"]
    stat: Literal["might", "speed", "wits"]
    skill: str


class ContestRollStep(BaseModel):
    type: Literal["contest"]
    stat: Literal["might", "speed", "wits"]
    skill: str
    defense_stat: Literal["might", "speed", "wits"]


class ApplyConditionStep(BaseModel):
    type: Literal["apply_condition"]
    target: ProcedureTarget
    condition_id: str
    duration_rounds: int
    when: ActionOutcome = "success"


class ApplyHealingStep(BaseModel):
    type: Literal["heal"]
    target: ProcedureTarget
    amount: int
    when: ActionOutcome = "success"


class ApplyStressStep(BaseModel):
    type: Literal["stress"]
    target: ProcedureTarget
    amount: int
    when: ActionOutcome = "success"


class ApplyAttackModifierStep(BaseModel):
    type: Literal["apply_attack_modifier"]
    target: ProcedureTarget
    amount: int
    duration_rounds: int
    when: ActionOutcome = "success"


class ClearConditionStep(BaseModel):
    type: Literal["clear_condition"]
    target: ProcedureTarget
    condition_id: str
    when: ActionOutcome = "always"


class MoveTargetStep(BaseModel):
    type: Literal["move_target"]
    target: Literal["target"] = "target"
    destination: MoveDestination = "choice"
    when: ActionOutcome = "success"


ActionProcedureStep = Annotated[
    AttackRollStep
    | CheckRollStep
    | ContestRollStep
    | ApplyConditionStep
    | ApplyHealingStep
    | ApplyStressStep
    | ApplyAttackModifierStep
    | ClearConditionStep
    | MoveTargetStep,
    Field(discriminator="type"),
]


class ActionProcedure(BaseModel):
    steps: list[ActionProcedureStep] = Field(default_factory=list)


ActionEffect = (
    AttackEffect
    | HealEffect
    | BuffEffect
    | StressEffect
    | DebuffAttackEffect
    | ContestDebuffEffect
    | ContestConditionEffect
    | ContestMoveEffect
    | RemoveConditionEffect
)


class ActionDefinition(BaseModel):
    id: str
    name: str
    action_cost: int
    tags: list[str]
    range: Literal["engaged", "near", "far", "self", "ally", "enemy"]
    allow_push: bool
    effect: ActionEffect = Field(discriminator="type")
    procedure: ActionProcedure | None = None


def attack_step_for_action(action: ActionDefinition) -> AttackRollStep | None:
    if action.procedure is not None:
        for step in action.procedure.steps:
            if isinstance(step, AttackRollStep):
                return step
    if isinstance(action.effect, AttackEffect):
        return AttackRollStep(
            type="attack",
            uses_weapon=action.effect.uses_weapon,
            weapon_id=action.effect.weapon_id,
            stat=action.effect.stat,
            skill=action.effect.skill,
        )
    return None


def attack_effect_from_step(step: AttackRollStep) -> AttackEffect:
    return AttackEffect(
        type="attack",
        uses_weapon=step.uses_weapon,
        weapon_id=step.weapon_id,
        stat=step.stat,
        skill=step.skill,
    )


def action_target_mode(action: ActionDefinition) -> Literal["self", "ally", "enemy"]:
    if action.range == "self":
        return "self"
    if action.range == "ally":
        return "ally"
    return "enemy"


def requires_destination_choice(action: ActionDefinition) -> bool:
    if action.procedure is not None:
        return any(isinstance(step, MoveTargetStep) for step in action.procedure.steps)
    return isinstance(action.effect, ContestMoveEffect)


def action_has_heal_steps(action: ActionDefinition) -> bool:
    if action.procedure is not None:
        return any(isinstance(step, ApplyHealingStep) for step in action.procedure.steps)
    return isinstance(action.effect, HealEffect)


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
    ammo_kind: str | None = None


class TalentEffect(BaseModel):
    type: Literal["final_girl", "healing_hands"]


class TalentDefinition(BaseModel):
    id: str
    name: str
    tags: list[str]
    effect: TalentEffect


DeathMode = Literal["pc_track", "die_at_zero"]
StressMode = Literal["track", "ignore"]


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
    death_mode: DeathMode = "pc_track"
    stress_mode: StressMode = "track"
    starting_band: Literal["engaged", "near", "far"] = "near"
    starting_ammo: dict[str, int] = Field(default_factory=dict)
    starting_bandages: int = 0
    starting_medkits: int = 0


class AreaDefinition(BaseModel):
    id: str
    name: str
    tags: list[str] = Field(default_factory=list)
    occupancy_limit: int | None = None


class ConnectionDefinition(BaseModel):
    id: str
    from_area: str
    to_area: str
    tags: list[str] = Field(default_factory=list)
    bidirectional: bool = True


class ObjectiveDefinition(BaseModel):
    type: Literal["defeat_enemies", "reach_exit", "hold_out"] = "defeat_enemies"
    area_id: str | None = None
    rounds: int | None = None
    team: Literal["team_a", "team_b"] = "team_a"


class ScenarioSideEntry(BaseModel):
    template_id: str
    persona_id: str | None = None
    count: int = 1
    start_area: str | None = None


class ScenarioDefinition(BaseModel):
    id: str
    name: str
    description: str
    areas: list[AreaDefinition] = Field(default_factory=list)
    connections: list[ConnectionDefinition] = Field(default_factory=list)
    objective: ObjectiveDefinition = Field(default_factory=ObjectiveDefinition)
    team_a: list[ScenarioSideEntry]
    team_b: list[ScenarioSideEntry]

    @model_validator(mode="after")
    def _normalize_legacy_layout(self) -> ScenarioDefinition:
        if not self.areas:
            self.areas = [AreaDefinition(id="arena", name="Arena")]
        default_area = self.areas[0].id
        normalized_team_a: list[ScenarioSideEntry] = []
        normalized_team_b: list[ScenarioSideEntry] = []
        for entry in self.team_a:
            if entry.start_area is None:
                entry = entry.model_copy(update={"start_area": default_area})
            normalized_team_a.append(entry)
        for entry in self.team_b:
            if entry.start_area is None:
                entry = entry.model_copy(update={"start_area": default_area})
            normalized_team_b.append(entry)
        self.team_a = normalized_team_a
        self.team_b = normalized_team_b
        return self


class BenchmarkSuite(BaseModel):
    id: str
    name: str
    scenario_ids: list[str]


class SessionPlan(BaseModel):
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
