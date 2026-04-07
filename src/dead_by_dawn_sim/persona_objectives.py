from __future__ import annotations

from typing import Protocol

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.rules import Ruleset
from dead_by_dawn_sim.state import ActorState, ActorStatus, EncounterState, shortest_path_distance


class ScoredPersona(Protocol):
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
    choice: ActionChoice, state: EncounterState, ruleset: Ruleset, persona: ScoredPersona
) -> float:
    actor = state.actor(choice.actor_id)
    enemies = _active_enemies(state, actor.team)
    if len(enemies) != 1:
        return 0.0
    last_enemy = enemies[0]
    movement_adjustment = _closeout_movement_adjustment(choice, state, actor, last_enemy, persona)
    if movement_adjustment is not None:
        return movement_adjustment
    return _closeout_nonmovement_adjustment(choice, state, ruleset, persona, actor, last_enemy)


def _closeout_movement_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    actor: ActorState,
    last_enemy: ActorState,
    persona: ScoredPersona,
) -> float | None:
    if choice.action_id in {"advance", "fall_back"} and choice.destination_area is not None:
        before = shortest_path_distance(state, actor.area_id, last_enemy.area_id)
        after = shortest_path_distance(state, choice.destination_area, last_enemy.area_id)
        if before is not None and after is not None and after < before:
            return persona.weights.get("closeout_pursuit", 3.0) * (before - after)
        return 0.0
    if choice.action_id == "stand_up":
        return -persona.weights.get("closeout_delay", 2.0)
    return None


def _closeout_nonmovement_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    persona: ScoredPersona,
    actor: ActorState,
    last_enemy: ActorState,
) -> float:
    action = ruleset.actions[choice.action_id]
    target = state.actor(choice.target_id)
    if target.actor_id == last_enemy.actor_id:
        return _closeout_enemy_target_adjustment(choice, action.tags, persona)
    if "heal" in action.tags and target.status.value in {"wounded", "critical", "stable"}:
        return persona.weights.get("closeout_rescue", 1.5)
    if choice.action_id == "rally" and target.actor_id != actor.actor_id:
        if target.status.value in {"wounded", "critical", "stable"}:
            return persona.weights.get("closeout_rescue", 1.0)
        return -persona.weights.get("closeout_rally_penalty", 4.0)
    return -persona.weights.get("closeout_delay", 2.0)


def _closeout_enemy_target_adjustment(
    choice: ActionChoice, action_tags: list[str], persona: ScoredPersona
) -> float:
    if "attack" in action_tags:
        return persona.weights.get("closeout_attack", 3.5)
    if choice.action_id == "trip":
        return -persona.weights.get("closeout_trip_penalty", 3.5)
    if choice.action_id == "feint" or "control" in action_tags or "stress" in action_tags:
        return -persona.weights.get("closeout_delay", 2.0)
    return 0.0


def objective_adjustment(
    choice: ActionChoice, state: EncounterState, persona: ScoredPersona
) -> float:
    actor = state.actor(choice.actor_id)
    objective = state.objective
    if objective.type == "reach_exit" and objective.area_id is not None:
        return _reach_exit_adjustment(
            choice, state, actor, objective.area_id, objective.team, persona
        )
    if objective.type == "hold_out" and objective.area_id is not None:
        return _hold_out_adjustment(
            choice, state, actor, objective.area_id, objective.team, persona
        )
    return 0.0


def _reach_exit_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    actor: ActorState,
    exit_area: str,
    runner_team: str,
    persona: ScoredPersona,
) -> float:
    if actor.team == runner_team:
        return _runner_reach_exit_adjustment(choice, state, actor, exit_area, persona)
    return _interceptor_reach_exit_adjustment(choice, state, actor, exit_area, runner_team, persona)


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
    actor: ActorState,
    exit_area: str,
    persona: ScoredPersona,
) -> float:
    if choice.action_id in {"advance", "fall_back"}:
        distance_delta = _movement_distance_delta(state, actor, choice.destination_area, exit_area)
        if distance_delta is not None:
            return distance_delta * persona.weights.get("objective_progress", 3.0)
    distance = shortest_path_distance(state, actor.area_id, exit_area)
    if choice.action_id not in {"advance", "fall_back"} and actor.area_id == exit_area:
        return persona.weights.get("hold_exit", 1.5)
    if _is_objective_delay(choice, actor, exit_area, distance):
        if distance is None:
            return 0.0
        return -distance * persona.weights.get("objective_delay_penalty", 2.2)
    return 0.0


def _is_objective_delay(
    choice: ActionChoice, actor: ActorState, exit_area: str, distance: int | None
) -> bool:
    return (
        choice.action_id not in {"advance", "fall_back", "stand_up"}
        and actor.area_id != exit_area
        and not actor.engaged_with
        and distance is not None
    )


def _interceptor_reach_exit_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    actor: ActorState,
    exit_area: str,
    runner_team: str,
    persona: ScoredPersona,
) -> float:
    movement_score = _intercept_movement_adjustment(choice, state, actor, exit_area, persona)
    if movement_score != 0.0:
        return movement_score
    target = state.actor(choice.target_id)
    target_distance = shortest_path_distance(state, target.area_id, exit_area)
    if target.team == runner_team and target_distance == 0:
        return persona.weights.get("deny_objective", 2.5)
    if target.team == runner_team and target_distance == 1:
        return persona.weights.get("intercept_runner", 1.2)
    return 0.0


def _intercept_movement_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    actor: ActorState,
    exit_area: str,
    persona: ScoredPersona,
) -> float:
    if choice.action_id in {"advance", "fall_back"}:
        distance_delta = _movement_distance_delta(state, actor, choice.destination_area, exit_area)
        if distance_delta is not None:
            return distance_delta * persona.weights.get("objective_intercept", 2.0)
    return 0.0


def _hold_out_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    actor: ActorState,
    hold_area: str,
    holder_team: str,
    persona: ScoredPersona,
) -> float:
    if choice.action_id in {"advance", "fall_back"}:
        distance_delta = _movement_distance_delta(state, actor, choice.destination_area, hold_area)
        if distance_delta is not None:
            weight_key = (
                "objective_progress" if actor.team == holder_team else "objective_intercept"
            )
            return distance_delta * persona.weights.get(weight_key, 2.0)
    if actor.area_id == hold_area:
        return persona.weights.get("hold_ground", 1.0 if actor.team == holder_team else 0.5)
    return 0.0
