from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

RESOURCE_IDS = frozenset({"bandages", "medkits", "sidearm"})
CONDITION_IDS = frozenset({"bleeding", "feinting", "inspired", "prone", "rattled", "steadied"})
ACTION_TAGS = frozenset(
    {
        "attack",
        "control",
        "heal",
        "movement",
        "positioning",
        "recovery",
        "reposition",
        "retreat",
        "self_sustain",
        "setup",
        "stress",
        "support",
    }
)
CONDITION_TAGS = frozenset(
    {"attack_buff", "attack_debuff", "damage_over_time", "positioning", "setup", "stabilized"}
)
WEAPON_TAGS = frozenset({"bleed"})
TALENT_TAGS = frozenset({"healing", "survival"})
TALENT_EFFECT_TYPES = frozenset({"auto_critical_heal", "revive_on_zero"})

ConditionId = Literal["bleeding", "feinting", "inspired", "prone", "rattled", "steadied"]
ResourceId = Literal["bandages", "medkits", "sidearm"]
DeathMode = Literal["pc_track", "die_at_zero"]
StressMode = Literal["track", "ignore"]


class DifficultyRules(BaseModel):
    challenging: int = Field(ge=1)
    formidable: int = Field(ge=1)


class PushRules(BaseModel):
    extra_die: int = Field(default=1, ge=1)
    keep: int = Field(default=2, ge=1)


class StressRules(BaseModel):
    starting: int = Field(ge=0)
    panic_threshold: int = Field(ge=0)
    breakdown_threshold: int = Field(ge=0)


class DeathRules(BaseModel):
    wounded_to_critical_difficulty: Literal["challenging", "formidable"]
    critical_stabilize_difficulty: Literal["challenging", "formidable"]
    shrouds_to_die: int = Field(ge=1)


class CoreRules(BaseModel):
    version: str = Field(min_length=1)
    check_dice: int = Field(ge=1)
    save_dice: int = Field(ge=1)
    keep_dice: int = Field(ge=1)
    hp_base: int = Field(ge=1)
    defense_base: int = Field(ge=0)
    crit_on_doubles: bool
    difficulties: DifficultyRules
    push: PushRules
    stress: StressRules
    death: DeathRules
    max_rounds: int = Field(default=10, ge=1)


class ConditionDefinition(BaseModel):
    id: ConditionId
    name: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    attack_modifier: int = 0
    damage_per_turn: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _validate_tags(self) -> ConditionDefinition:
        unknown = sorted(set(self.tags) - CONDITION_TAGS)
        if unknown:
            raise ValueError(f"Condition {self.id} uses unknown tags: {', '.join(unknown)}.")
        if len(self.tags) != len(set(self.tags)):
            raise ValueError(f"Condition {self.id} repeats tag values.")
        return self


class WeaponDefinition(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    skill: str = Field(min_length=1)
    damage_die: int = Field(ge=1)
    tags: list[str] = Field(default_factory=list)
    max_range: Literal["engaged", "near", "far"]
    ammo_kind: ResourceId | None = None

    @model_validator(mode="after")
    def _validate_tags(self) -> WeaponDefinition:
        unknown = sorted(set(self.tags) - WEAPON_TAGS)
        if unknown:
            raise ValueError(f"Weapon {self.id} uses unknown tags: {', '.join(unknown)}.")
        if len(self.tags) != len(set(self.tags)):
            raise ValueError(f"Weapon {self.id} repeats tag values.")
        return self


class TalentEffect(BaseModel):
    type: Literal["auto_critical_heal", "revive_on_zero"]
    key: str | None = Field(default=None, min_length=1)
    once_per_actor: bool = False
    amount: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _validate_effect(self) -> TalentEffect:
        if self.key is None:
            self.key = self.type
        if self.type == "revive_on_zero" and self.amount is None:
            raise ValueError("Talent effect revive_on_zero requires an amount.")
        return self


class TalentDefinition(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    effect: TalentEffect

    @model_validator(mode="after")
    def _validate_tags(self) -> TalentDefinition:
        unknown = sorted(set(self.tags) - TALENT_TAGS)
        if unknown:
            raise ValueError(f"Talent {self.id} uses unknown tags: {', '.join(unknown)}.")
        if len(self.tags) != len(set(self.tags)):
            raise ValueError(f"Talent {self.id} repeats tag values.")
        return self


class ActorTemplate(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    default_policy: str = Field(min_length=1)
    stats: dict[Literal["might", "speed", "wits"], int]
    skills: dict[str, int]
    actions: list[str]
    weapon_id: str | None = Field(default=None, min_length=1)
    talents: list[str] = Field(default_factory=list)
    death_mode: DeathMode = "pc_track"
    stress_mode: StressMode = "track"
    starting_band: Literal["engaged", "near", "far"] = "near"
    starting_resources: dict[ResourceId, int] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_resources(self) -> ActorTemplate:
        for resource_id, amount in self.starting_resources.items():
            if amount < 0:
                raise ValueError(f"Actor {self.id} cannot start with negative {resource_id}.")
        return self


class AreaDefinition(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    occupancy_limit: int | None = Field(default=None, ge=1)


class ConnectionDefinition(BaseModel):
    id: str = Field(min_length=1)
    from_area: str = Field(min_length=1)
    to_area: str = Field(min_length=1)
    tags: list[str] = Field(default_factory=list)
    bidirectional: bool = True


class ObjectiveDefinition(BaseModel):
    type: Literal["defeat_enemies", "reach_exit", "hold_out"] = "defeat_enemies"
    area_id: str | None = Field(default=None, min_length=1)
    rounds: int | None = Field(default=None, ge=1)
    team: Literal["team_a", "team_b"] = "team_a"


class ScenarioSideEntry(BaseModel):
    template_id: str = Field(min_length=1)
    policy_id: str | None = Field(default=None, min_length=1)
    count: int = Field(default=1, ge=1)
    start_area: str | None = Field(default=None, min_length=1)


class ScenarioDefinition(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
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
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    scenario_ids: list[str] = Field(default_factory=list, min_length=1)


class InterludeTreatmentRule(BaseModel):
    resource: ResourceId
    resource_cost: int = Field(default=1, ge=1)
    heal_amount: int = Field(default=1, ge=0)
    priority: Literal["lowest_hp_then_stress"] = "lowest_hp_then_stress"
    clear_conditions: bool = True
    restore_to_normal_on_heal: bool = True


class SessionInterlude(BaseModel):
    treatments: list[InterludeTreatmentRule] = Field(default_factory=list)


class SessionPlan(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    scenario_ids: list[str] = Field(default_factory=list, min_length=1)
    interlude: SessionInterlude = Field(default_factory=SessionInterlude)
