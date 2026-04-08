from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

ActionOutcome = Literal["always", "success", "critical"]
ProcedureTarget = Literal["self", "target"]
MoveDestination = Literal["choice"]
ReactionTiming = Literal["none", "before", "after"]


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


class SpendResourceStep(BaseModel):
    type: Literal["spend_resource"]
    resource: str
    amount: int = 1
    when: ActionOutcome = "always"


class SpendAmmoStep(BaseModel):
    type: Literal["spend_ammo"]
    amount: int = 1
    when: ActionOutcome = "always"


class ClearConditionStep(BaseModel):
    type: Literal["clear_condition"]
    target: ProcedureTarget
    condition_id: str
    when: ActionOutcome = "always"


class MoveTargetStep(BaseModel):
    type: Literal["move_target"]
    target: ProcedureTarget
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
    | SpendResourceStep
    | SpendAmmoStep
    | ClearConditionStep
    | MoveTargetStep,
    Field(discriminator="type"),
]


class HasConditionRequirement(BaseModel):
    type: Literal["has_condition"]
    condition_id: str


class MissingHpRequirement(BaseModel):
    type: Literal["missing_hp"]


class ResourceAtLeastRequirement(BaseModel):
    type: Literal["resource_at_least"]
    resource: str
    amount: int = 1


class AmmoAtLeastRequirement(BaseModel):
    type: Literal["ammo_at_least"]
    amount: int = 1


class EngagedRequirement(BaseModel):
    type: Literal["engaged"]
    value: bool = True


ActionRequirement = Annotated[
    HasConditionRequirement
    | MissingHpRequirement
    | ResourceAtLeastRequirement
    | AmmoAtLeastRequirement
    | EngagedRequirement,
    Field(discriminator="type"),
]


class ActionAvailability(BaseModel):
    universal: bool = False
    all_of: list[ActionRequirement] = Field(default_factory=list)
    any_of: list[ActionRequirement] = Field(default_factory=list)


class ActionProcedure(BaseModel):
    steps: list[ActionProcedureStep] = Field(default_factory=list)


class ActionDefinition(BaseModel):
    id: str
    name: str
    action_cost: int
    tags: list[str]
    range: Literal["engaged", "near", "far", "self", "ally", "enemy"]
    allow_push: bool
    procedure: ActionProcedure
    availability: ActionAvailability = Field(default_factory=ActionAvailability)
    reaction_timing: ReactionTiming = "none"


def attack_step_for_action(action: ActionDefinition) -> AttackRollStep | None:
    for step in action.procedure.steps:
        if isinstance(step, AttackRollStep):
            return step
    return None


def move_step_for_action(action: ActionDefinition) -> MoveTargetStep | None:
    for step in action.procedure.steps:
        if isinstance(step, MoveTargetStep):
            return step
    return None


def action_target_mode(action: ActionDefinition) -> Literal["self", "ally", "enemy"]:
    if action.range == "self":
        return "self"
    if action.range == "ally":
        return "ally"
    return "enemy"


def requires_destination_choice(action: ActionDefinition) -> bool:
    return move_step_for_action(action) is not None


def action_has_heal_steps(action: ActionDefinition) -> bool:
    return any(isinstance(step, ApplyHealingStep) for step in action.procedure.steps)
