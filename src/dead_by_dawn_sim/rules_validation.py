from __future__ import annotations

from dead_by_dawn_sim.rules import (
    ApplyConditionStep,
    AttackRollStep,
    ClearConditionStep,
    Ruleset,
)


def _validate_actor_templates(ruleset: Ruleset) -> None:
    for actor in ruleset.actors.values():
        for action_id in actor.actions:
            if action_id not in ruleset.actions:
                raise ValueError(f"Actor {actor.id} references unknown action {action_id}.")
        if actor.weapon_id is not None and actor.weapon_id not in ruleset.weapons:
            raise ValueError(f"Actor {actor.id} references unknown weapon {actor.weapon_id}.")
        for ammo_kind in actor.starting_ammo:
            if not ammo_kind:
                raise ValueError(f"Actor {actor.id} has an empty ammo kind key.")
        for talent_id in actor.talents:
            if talent_id not in ruleset.talents:
                raise ValueError(f"Actor {actor.id} references unknown talent {talent_id}.")


def _validate_action_procedure(ruleset: Ruleset, action_id: str) -> None:
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
    _validate_scenarios(ruleset)
    _validate_suites_and_plans(ruleset)
