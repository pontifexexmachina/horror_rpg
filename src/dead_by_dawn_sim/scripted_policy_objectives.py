from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from dead_by_dawn_sim.rules import (
    ActionDefinition,
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


def _active_enemies(state: EncounterState, team: str) -> list[ActorState]:
    return [
        candidate
        for candidate in state.actors.values()
        if candidate.team != team
        and candidate.status
        not in {ActorStatus.DEAD, ActorStatus.CRITICAL, ActorStatus.STABLE, ActorStatus.BROKEN}
    ]


def closeout_adjustment(
    choice: ActionChoice, state: EncounterState, ruleset: Ruleset, policy: ScoredPolicy
) -> float:
    actor = state.actor(choice.actor_id)
    enemies = _active_enemies(state, actor.team)
    if len(enemies) != 1:
        return 0.0
    last_enemy = enemies[0]
    movement_adjustment = _closeout_movement_adjustment(
        choice, state, ruleset, actor, last_enemy, policy
    )
    if movement_adjustment is not None:
        return movement_adjustment
    return _closeout_nonmovement_adjustment(choice, state, ruleset, policy, actor, last_enemy)


def _closeout_movement_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    actor: ActorState,
    last_enemy: ActorState,
    policy: ScoredPolicy,
) -> float | None:
    action = ruleset.actions[choice.action_id]
    if action_is_movement(action) and choice.destination_area is not None:
        before = shortest_path_distance(state, actor.area_id, last_enemy.area_id)
        after = shortest_path_distance(state, choice.destination_area, last_enemy.area_id)
        if before is not None and after is not None and after < before:
            return policy.weights.get("closeout_pursuit", 3.0) * (before - after)
        return 0.0
    if action_has_behavior(action, "stand_up"):
        return -policy.weights.get("closeout_delay", 2.0)
    return None


def _closeout_nonmovement_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    policy: ScoredPolicy,
    actor: ActorState,
    last_enemy: ActorState,
) -> float:
    action = ruleset.actions[choice.action_id]
    target = state.actor(choice.target_id)
    if target.actor_id == last_enemy.actor_id:
        return _closeout_enemy_target_adjustment(action, policy)
    if action_is_heal(action) and target.status.value in {"wounded", "critical", "stable"}:
        return policy.weights.get("closeout_rescue", 1.5)
    if action_has_behavior(action, "ally_support") and target.actor_id != actor.actor_id:
        if target.status.value in {"wounded", "critical", "stable"}:
            return policy.weights.get("closeout_rescue", 1.0)
        return -policy.weights.get("closeout_rally_penalty", 4.0)
    return -policy.weights.get("closeout_delay", 2.0)


def _closeout_enemy_target_adjustment(
    action: ActionDefinition,
    policy: ScoredPolicy,
) -> float:
    if action_is_attack(action):
        return policy.weights.get("closeout_attack", 3.5)
    if action_has_behavior(action, "control_setup"):
        return -policy.weights.get("closeout_trip_penalty", 3.5)
    if action_has_behavior(action, "control_reposition") or action_is_stress(action):
        return -policy.weights.get("closeout_delay", 2.0)
    return 0.0


def objective_adjustment(
    choice: ActionChoice, state: EncounterState, ruleset: Ruleset, policy: ScoredPolicy
) -> float:
    actor = state.actor(choice.actor_id)
    objective = state.objective
    if objective.type == "reach_exit" and objective.area_id is not None:
        return _reach_exit_adjustment(
            choice, state, ruleset, actor, objective.area_id, objective.team, policy
        )
    if objective.type == "hold_out" and objective.area_id is not None:
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


def _movement_distance_delta(
    state: EncounterState,
    actor: ActorState,
    destination_area: str | None,
    goal_area: str,
) -> int | None:
    if destination_area is None:
        return None
    before = shortest_path_distance(state, actor.area_id, goal_area)
    after = shortest_path_distance(state, destination_area, goal_area)
    if before is None or after is None:
        return None
    return before - after


def _runner_reach_exit_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    actor: ActorState,
    exit_area: str,
    policy: ScoredPolicy,
) -> float:
    if _is_movement_choice(choice, ruleset):
        distance_delta = _movement_distance_delta(state, actor, choice.destination_area, exit_area)
        if distance_delta is not None:
            return distance_delta * policy.weights.get("objective_progress", 3.0)
    distance = shortest_path_distance(state, actor.area_id, exit_area)
    if not _is_movement_choice(choice, ruleset) and actor.area_id == exit_area:
        return policy.weights.get("hold_exit", 1.5)
    if _is_objective_delay(choice, ruleset, actor, exit_area, distance):
        if distance is None:
            return 0.0
        return -distance * policy.weights.get("objective_delay_penalty", 2.2)
    return 0.0


def _is_objective_delay(
    choice: ActionChoice,
    ruleset: Ruleset,
    actor: ActorState,
    exit_area: str,
    distance: int | None,
) -> bool:
    return (
        not _is_movement_choice(choice, ruleset)
        and not _is_self_recovery_choice(choice, ruleset)
        and actor.area_id != exit_area
        and not actor.engaged_with
        and distance is not None
    )


def _interceptor_reach_exit_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    actor: ActorState,
    exit_area: str,
    runner_team: str,
    policy: ScoredPolicy,
) -> float:
    movement_score = _intercept_movement_adjustment(choice, state, ruleset, actor, exit_area, policy)
    if movement_score != 0.0:
        return movement_score
    target = state.actor(choice.target_id)
    target_distance = shortest_path_distance(state, target.area_id, exit_area)
    if target.team == runner_team and target_distance == 0:
        return policy.weights.get("deny_objective", 2.5)
    if target.team == runner_team and target_distance == 1:
        return policy.weights.get("intercept_runner", 1.2)
    return 0.0


def _intercept_movement_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    actor: ActorState,
    exit_area: str,
    policy: ScoredPolicy,
) -> float:
    if _is_movement_choice(choice, ruleset):
        distance_delta = _movement_distance_delta(state, actor, choice.destination_area, exit_area)
        if distance_delta is not None:
            return distance_delta * policy.weights.get("objective_intercept", 2.0)
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
    if _is_movement_choice(choice, ruleset):
        distance_delta = _movement_distance_delta(state, actor, choice.destination_area, hold_area)
        if distance_delta is not None:
            weight_key = (
                "objective_progress" if actor.team == holder_team else "objective_intercept"
            )
            return distance_delta * policy.weights.get(weight_key, 2.0)
    if actor.area_id == hold_area:
        return policy.weights.get("hold_ground", 1.0 if actor.team == holder_team else 0.5)
    return 0.0


def _is_movement_choice(choice: ActionChoice, ruleset: Ruleset) -> bool:
    return action_is_movement(ruleset.actions[choice.action_id])


def _is_self_recovery_choice(choice: ActionChoice, ruleset: Ruleset) -> bool:
    action = ruleset.actions[choice.action_id]
    return action_has_behavior(action, "stand_up")
