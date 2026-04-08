from __future__ import annotations

from dead_by_dawn_sim.rules import (
    ApplyAttackModifierStep,
    ApplyConditionStep,
    ApplyHealingStep,
    ApplyStressStep,
    AttackRollStep,
    ClearConditionStep,
    MoveTargetStep,
    Ruleset,
)
from dead_by_dawn_sim.rules_content_models import ACTION_TAGS, RESOURCE_IDS, TALENT_EFFECT_TYPES


def _validate_actor_templates(ruleset: Ruleset) -> None:
    for actor in ruleset.actors.values():
        for action_id in actor.actions:
            if action_id not in ruleset.actions:
                raise ValueError(f"Actor {actor.id} references unknown action {action_id}.")
        if actor.weapon_id is not None and actor.weapon_id not in ruleset.weapons:
            raise ValueError(f"Actor {actor.id} references unknown weapon {actor.weapon_id}.")
        for talent_id in actor.talents:
            if talent_id not in ruleset.talents:
                raise ValueError(f"Actor {actor.id} references unknown talent {talent_id}.")
        for resource_id in actor.starting_resources:
            if resource_id not in RESOURCE_IDS:
                raise ValueError(f"Actor {actor.id} references unknown resource {resource_id}.")


def _validate_action_tags(action_id: str, tags: list[str]) -> None:
    unknown = sorted(set(tags) - ACTION_TAGS)
    if unknown:
        raise ValueError(f"Action {action_id} uses unknown tags: {', '.join(unknown)}.")
    if len(tags) != len(set(tags)):
        raise ValueError(f"Action {action_id} repeats tag values.")


def _validate_action_tag_expectations(
    action_id: str,
    tags: list[str],
    *,
    has_attack_step: bool,
    has_heal_step: bool,
    has_stress_step: bool,
    has_move_step: bool,
    has_condition_step: bool,
    has_control_effect: bool,
    action_range: str,
) -> None:
    if "attack" in tags and not has_attack_step:
        raise ValueError(f"Action {action_id} is tagged attack but has no attack step.")
    if "heal" in tags and not has_heal_step:
        raise ValueError(f"Action {action_id} is tagged heal but has no heal step.")
    if "stress" in tags and not has_stress_step:
        raise ValueError(f"Action {action_id} is tagged stress but has no stress step.")
    if any(tag in tags for tag in {"movement", "reposition", "retreat"}) and not has_move_step:
        raise ValueError(f"Action {action_id} uses movement-style tags but has no move_target step.")
    if "recovery" in tags and not has_condition_step:
        raise ValueError(f"Action {action_id} is tagged recovery but has no condition step.")
    if "self_sustain" in tags and action_range != "self":
        raise ValueError(f"Action {action_id} is tagged self_sustain but is not self-targeted.")
    if "control" in tags and not has_control_effect:
        raise ValueError(f"Action {action_id} is tagged control but has no control effect step.")


def _validate_action_references(ruleset: Ruleset, action_id: str) -> None:
    action = ruleset.actions[action_id]
    for step in action.procedure.steps:
        step_condition_id = None
        if isinstance(step, ApplyConditionStep | ClearConditionStep):
            step_condition_id = step.condition_id
        if step_condition_id is not None and step_condition_id not in ruleset.conditions:
            raise ValueError(
                f"Action {action.id} procedure references unknown condition {step_condition_id}."
            )
        if (
            isinstance(step, AttackRollStep)
            and step.weapon_id is not None
            and step.weapon_id not in ruleset.weapons
        ):
            raise ValueError(
                f"Action {action.id} procedure references unknown weapon {step.weapon_id}."
            )


def _validate_action_procedure(ruleset: Ruleset, action_id: str) -> None:
    action = ruleset.actions[action_id]
    _validate_action_tags(action.id, action.tags)
    step_types = {type(step) for step in action.procedure.steps}
    _validate_action_tag_expectations(
        action.id,
        action.tags,
        has_attack_step=AttackRollStep in step_types,
        has_heal_step=ApplyHealingStep in step_types,
        has_stress_step=ApplyStressStep in step_types,
        has_move_step=MoveTargetStep in step_types,
        has_condition_step=ApplyConditionStep in step_types or ClearConditionStep in step_types,
        has_control_effect=(
            MoveTargetStep in step_types
            or ApplyConditionStep in step_types
            or ClearConditionStep in step_types
            or ApplyStressStep in step_types
            or ApplyAttackModifierStep in step_types
        ),
        action_range=action.range,
    )
    _validate_action_references(ruleset, action_id)


def _validate_actions(ruleset: Ruleset) -> None:
    for action in ruleset.actions.values():
        _validate_action_procedure(ruleset, action.id)


def _validate_scenarios(ruleset: Ruleset) -> None:
    for scenario in ruleset.scenarios.values():
        area_ids = [area.id for area in scenario.areas]
        if len(area_ids) != len(set(area_ids)):
            raise ValueError(f"Scenario {scenario.id} defines duplicate area ids.")
        area_id_set = set(area_ids)
        for side in [scenario.team_a, scenario.team_b]:
            for entry in side:
                if entry.template_id not in ruleset.actors:
                    msg = (
                        f"Scenario {scenario.id} references unknown actor template "
                        f"{entry.template_id}."
                    )
                    raise ValueError(msg)
                if entry.start_area not in area_id_set:
                    raise ValueError(
                        f"Scenario {scenario.id} references unknown start area {entry.start_area}."
                    )
        for connection in scenario.connections:
            if connection.from_area not in area_id_set or connection.to_area not in area_id_set:
                raise ValueError(
                    f"Scenario {scenario.id} has a connection with an unknown area endpoint."
                )
        if scenario.objective.area_id is not None and scenario.objective.area_id not in area_id_set:
            raise ValueError(
                f"Scenario {scenario.id} objective references unknown area {scenario.objective.area_id}."
            )


def _validate_talents(ruleset: Ruleset) -> None:
    for talent in ruleset.talents.values():
        if talent.effect.type not in TALENT_EFFECT_TYPES:
            raise ValueError(f"Talent {talent.id} uses unknown effect type {talent.effect.type}.")
        if talent.effect.type == "revive_on_zero" and talent.effect.amount is None:
            raise ValueError(f"Talent {talent.id} requires an amount for revive_on_zero.")


def _validate_suites_and_plans(ruleset: Ruleset) -> None:
    for suite in ruleset.benchmark_suites.values():
        for scenario_id in suite.scenario_ids:
            if scenario_id not in ruleset.scenarios:
                msg = f"Benchmark suite {suite.id} references unknown scenario {scenario_id}."
                raise ValueError(msg)
    for plan in ruleset.session_plans.values():
        for scenario_id in plan.scenario_ids:
            if scenario_id not in ruleset.scenarios:
                raise ValueError(
                    f"Session plan {plan.id} references unknown scenario {scenario_id}."
                )


def validate_ruleset(ruleset: Ruleset) -> None:
    _validate_actor_templates(ruleset)
    _validate_actions(ruleset)
    _validate_talents(ruleset)
    _validate_scenarios(ruleset)
    _validate_suites_and_plans(ruleset)
