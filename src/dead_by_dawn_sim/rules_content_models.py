from __future__ import annotations

from typing import Literal

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
    type: str
    key: str | None = None
    once_per_actor: bool = False
    amount: int | None = None

    @model_validator(mode="after")
    def _default_key(self) -> TalentEffect:
        if self.key is None:
            self.key = self.type
        return self

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
    default_policy: str
    stats: dict[Literal["might", "speed", "wits"], int]
    skills: dict[str, int]
    actions: list[str]
    weapon_id: str | None = None
    talents: list[str] = Field(default_factory=list)
    death_mode: DeathMode = "pc_track"
    stress_mode: StressMode = "track"
    starting_band: Literal["engaged", "near", "far"] = "near"
    starting_resources: dict[str, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_resources(self) -> ActorTemplate:
        for resource_id in self.starting_resources:
            if not resource_id:
                raise ValueError("Actor starting resource ids must be non-empty.")
        return self


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
    policy_id: str | None = None
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


class InterludeTreatmentRule(BaseModel):
    resource: str
    resource_cost: int = 1
    heal_amount: int = 1
    priority: Literal["lowest_hp_then_stress"] = "lowest_hp_then_stress"
    clear_conditions: bool = True
    restore_to_normal_on_heal: bool = True

    @model_validator(mode="after")
    def _validate_resource(self) -> InterludeTreatmentRule:
        if not self.resource:
            raise ValueError("Interlude treatment resource must be non-empty.")
        return self


class SessionInterlude(BaseModel):
    treatments: list[InterludeTreatmentRule] = Field(default_factory=list)


class SessionPlan(BaseModel):
    id: str
    name: str
    scenario_ids: list[str]
    interlude: SessionInterlude = Field(default_factory=SessionInterlude)
