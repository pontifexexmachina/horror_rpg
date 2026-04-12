from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from dead_by_dawn_sim.rules import (
    Ruleset,
    action_has_behavior,
    action_is_attack,
    action_is_heal,
    action_is_movement,
    action_is_stress,
)
from dead_by_dawn_sim.state import ActorState, ActorStatus, EncounterState, shortest_path_distance

if TYPE_CHECKING:
    from dead_by_dawn_sim.actions import ActionChoice


class ScoredPolicy(Protocol):
    @property
    def weights(self) -> dict[str, float]: ...


_NONACTIVE = {ActorStatus.DEAD, ActorStatus.CRITICAL, ActorStatus.STABLE, ActorStatus.BROKEN}
_RESCUE_STATUSES = {"wounded", "critical", "stable"}


def _objective_movement_score(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    actor: ActorState,
    goal_area: str,
    policy: ScoredPolicy,
    weight_key: str,
) -> float:
    if not action_is_movement(ruleset.actions[choice.action_id]) or choice.destination_area is None:
        return 0.0
    before = shortest_path_distance(state, actor.area_id, goal_area)
    after = shortest_path_distance(state, choice.destination_area, goal_area)
    if before is None or after is None:
        return 0.0
    return (before - after) * policy.weights.get(weight_key, 0.0)


def _active_enemies(state: EncounterState, team: str) -> list[ActorState]:
    return [
        candidate
        for candidate in state.actors.values()
        if candidate.team != team and candidate.status not in _NONACTIVE
    ]


def closeout_adjustment(
    choice: ActionChoice, state: EncounterState, ruleset: Ruleset, policy: ScoredPolicy
) -> float:
    actor = state.actor(choice.actor_id)
    enemies = _active_enemies(state, actor.team)
    if len(enemies) != 1:
        return 0.0
    last_enemy = enemies[0]
    action = ruleset.actions[choice.action_id]
    movement_score = _objective_movement_score(
        choice, state, ruleset, actor, last_enemy.area_id, policy, "closeout_pursuit"
    )
    if action_is_movement(action):
        return max(0.0, movement_score)
    if action_has_behavior(action, "stand_up"):
        return -policy.weights.get("closeout_delay", 2.0)
    return _closeout_nonmovement_adjustment(choice, state, ruleset, policy, actor, last_enemy)


def _closeout_enemy_target_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    policy: ScoredPolicy,
    last_enemy: ActorState,
) -> float | None:
    action = ruleset.actions[choice.action_id]
    if state.actor(choice.target_id).actor_id != last_enemy.actor_id:
        return None
    if action_is_attack(action):
        return policy.weights.get("closeout_attack", 3.5)
    if action_has_behavior(action, "control_setup"):
        return -policy.weights.get("closeout_trip_penalty", 3.5)
    if action_has_behavior(action, "control_reposition") or action_is_stress(action):
        return -policy.weights.get("closeout_delay", 2.0)
    return 0.0


def _closeout_nonmovement_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    policy: ScoredPolicy,
    actor: ActorState,
    last_enemy: ActorState,
) -> float:
    target_score = _closeout_enemy_target_adjustment(choice, state, ruleset, policy, last_enemy)
    if target_score is not None:
        return target_score

    action = ruleset.actions[choice.action_id]
    target = state.actor(choice.target_id)
    if action_is_heal(action) and target.status.value in _RESCUE_STATUSES:
        return policy.weights.get("closeout_rescue", 1.5)
    if action_has_behavior(action, "ally_support") and target.actor_id != actor.actor_id:
        if target.status.value in _RESCUE_STATUSES:
            return policy.weights.get("closeout_rescue", 1.0)
        return -policy.weights.get("closeout_rally_penalty", 4.0)
    return -policy.weights.get("closeout_delay", 2.0)


def objective_adjustment(
    choice: ActionChoice, state: EncounterState, ruleset: Ruleset, policy: ScoredPolicy
) -> float:
    actor = state.actor(choice.actor_id)
    objective = state.objective
    if objective.area_id is None:
        return 0.0
    if objective.type == "reach_exit":
        return _reach_exit_adjustment(
            choice, state, ruleset, actor, objective.area_id, objective.team, policy
        )
    if objective.type == "hold_out":
        return _hold_out_adjustment(
            choice, state, ruleset, actor, objective.area_id, objective.team, policy
        )
    return 0.0


def _reach_exit_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    actor: ActorState,
    exit_area: str,
    runner_team: str,
    policy: ScoredPolicy,
) -> float:
    if actor.team == runner_team:
        return _runner_reach_exit_adjustment(choice, state, ruleset, actor, exit_area, policy)
    return _interceptor_reach_exit_adjustment(
        choice, state, ruleset, actor, exit_area, runner_team, policy
    )


def _runner_reach_exit_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    actor: ActorState,
    exit_area: str,
    policy: ScoredPolicy,
) -> float:
    action = ruleset.actions[choice.action_id]
    movement_score = _objective_movement_score(
        choice, state, ruleset, actor, exit_area, policy, "objective_progress"
    )
    if movement_score != 0.0:
        return movement_score
    distance = shortest_path_distance(state, actor.area_id, exit_area)
    if actor.area_id == exit_area and not action_is_movement(action):
        return policy.weights.get("hold_exit", 1.5)
    if (
        not action_is_movement(action)
        and not action_has_behavior(action, "stand_up")
        and actor.area_id != exit_area
        and not actor.engaged_with
        and distance is not None
    ):
        return -distance * policy.weights.get("objective_delay_penalty", 2.2)
    return 0.0


def _interceptor_reach_exit_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    actor: ActorState,
    exit_area: str,
    runner_team: str,
    policy: ScoredPolicy,
) -> float:
    movement_score = _objective_movement_score(
        choice, state, ruleset, actor, exit_area, policy, "objective_intercept"
    )
    if movement_score != 0.0:
        return movement_score
    target = state.actor(choice.target_id)
    target_distance = shortest_path_distance(state, target.area_id, exit_area)
    if target.team == runner_team and target_distance == 0:
        return policy.weights.get("deny_objective", 2.5)
    if target.team == runner_team and target_distance == 1:
        return policy.weights.get("intercept_runner", 1.2)
    return 0.0


def _hold_out_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    actor: ActorState,
    hold_area: str,
    holder_team: str,
    policy: ScoredPolicy,
) -> float:
    movement_score = _objective_movement_score(
        choice,
        state,
        ruleset,
        actor,
        hold_area,
        policy,
        "objective_progress" if actor.team == holder_team else "objective_intercept",
    )
    if movement_score != 0.0:
        return movement_score
    if actor.area_id == hold_area:
        return policy.weights.get("hold_ground", 1.0 if actor.team == holder_team else 0.5)
    return 0.0
