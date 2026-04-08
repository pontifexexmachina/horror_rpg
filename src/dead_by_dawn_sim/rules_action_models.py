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
    behavior_tags: list[str] = Field(default_factory=list)
    narration_id: str | None = None
    range: Literal["engaged", "near", "far", "self", "ally", "enemy"]
    allow_push: bool
    procedure: ActionProcedure
    availability: ActionAvailability = Field(default_factory=ActionAvailability)
    reaction_timing: ReactionTiming = "none"


def action_has_tag(action: ActionDefinition, tag: str) -> bool:
    return tag in action.tags


def action_has_behavior(action: ActionDefinition, behavior: str) -> bool:
    return behavior in action.behavior_tags


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


def action_is_attack(action: ActionDefinition) -> bool:
    return action_has_tag(action, "attack")


def action_is_control(action: ActionDefinition) -> bool:
    return action_has_tag(action, "control") or action_has_behavior(action, "control")


def action_is_heal(action: ActionDefinition) -> bool:
    return action_has_tag(action, "heal") or action_has_behavior(action, "self_heal")


def action_is_stress(action: ActionDefinition) -> bool:
    return action_has_tag(action, "stress") or action_has_behavior(action, "stress")


def action_is_movement(action: ActionDefinition) -> bool:
    return action_has_tag(action, "movement") or action_has_behavior(action, "movement")


def action_is_reposition(action: ActionDefinition) -> bool:
    return action_has_tag(action, "reposition") or action_has_behavior(action, "reposition")


def action_is_recovery(action: ActionDefinition) -> bool:
    return action_has_tag(action, "recovery") or action_has_behavior(action, "stand_up")


def action_clears_condition(
    action: ActionDefinition,
    condition_id: str,
    *,
    target: ProcedureTarget | None = None,
) -> bool:
    return any(
        isinstance(step, ClearConditionStep)
        and step.condition_id == condition_id
        and (target is None or step.target == target)
        for step in action.procedure.steps
    )


def requires_destination_choice(action: ActionDefinition) -> bool:
    return move_step_for_action(action) is not None


def action_has_heal_steps(action: ActionDefinition) -> bool:
    return any(isinstance(step, ApplyHealingStep) for step in action.procedure.steps)
