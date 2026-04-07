from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

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


class ActionDefinition(BaseModel):
    id: str
    name: str
    action_cost: int
    tags: list[str]
    range: Literal["engaged", "near", "far", "self", "ally", "enemy"]
    allow_push: bool
    procedure: ActionProcedure


def attack_step_for_action(action: ActionDefinition) -> AttackRollStep | None:
    for step in action.procedure.steps:
        if isinstance(step, AttackRollStep):
            return step
    return None


def action_target_mode(action: ActionDefinition) -> Literal["self", "ally", "enemy"]:
    if action.range == "self":
        return "self"
    if action.range == "ally":
        return "ally"
    return "enemy"


def requires_destination_choice(action: ActionDefinition) -> bool:
    return any(isinstance(step, MoveTargetStep) for step in action.procedure.steps)


def action_has_heal_steps(action: ActionDefinition) -> bool:
    return any(isinstance(step, ApplyHealingStep) for step in action.procedure.steps)
