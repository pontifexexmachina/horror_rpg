from __future__ import annotations

from dataclasses import dataclass

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.rules import Ruleset
from dead_by_dawn_sim.state import ActorState, EncounterState, shortest_path_distance


@dataclass(frozen=True)
class Persona:
    id: str
    weights: dict[str, float]
    push_threshold: float

    def choose_action(
        self, legal_actions: list[ActionChoice], state: EncounterState, ruleset: Ruleset
    ) -> ActionChoice:
        return max(legal_actions, key=lambda choice: _score_action(choice, state, ruleset, self))


def _score_action(
    choice: ActionChoice, state: EncounterState, ruleset: Ruleset, persona: Persona
) -> float:
    actor = state.actor(choice.actor_id)
    target = state.actor(choice.target_id)
    score = 0.0

    if choice.action_id in {"advance", "fall_back"}:
        score += persona.weights.get(choice.action_id, 0.0)
        if choice.action_id == "advance" and not _has_attack_option(
            state, ruleset, choice.actor_id
        ):
            score += persona.weights.get("close_distance", 0.0)
        if choice.action_id == "fall_back" and actor.hp <= max(2, actor.max_hp // 3):
            score += persona.weights.get("escape", 0.0)
    else:
        action = ruleset.actions[choice.action_id]
        for tag in action.tags:
            score += persona.weights.get(tag, 0.0)
        if target.hp <= max(2, target.max_hp // 3):
            score += persona.weights.get("finisher", 0.0)
        score += _context_adjustment(choice, state, ruleset, persona)
        if choice.push:
            score += persona.push_threshold
            score += _push_adjustment(actor, ruleset, persona)

    score += _objective_adjustment(choice, state, persona)

    if actor.hp <= max(2, actor.max_hp // 3):
        score += persona.weights.get("low_hp_modifier", 0.0)
    if actor.stress >= ruleset.core.stress.panic_threshold:
        score += persona.weights.get("high_stress_modifier", 0.0)
    return score


def _context_adjustment(
    choice: ActionChoice, state: EncounterState, ruleset: Ruleset, persona: Persona
) -> float:
    actor = state.actor(choice.actor_id)
    target = state.actor(choice.target_id)
    action = ruleset.actions[choice.action_id]
    adjustment = 0.0

    if "heal" in action.tags:
        missing_hp = target.max_hp - target.hp
        if missing_hp == 0:
            adjustment -= 4.0
        else:
            adjustment += missing_hp * persona.weights.get("heal_urgency", 0.2)
        if target.status.value in {"wounded", "critical"}:
            adjustment += persona.weights.get("rescue", 0.5)

    if "stabilize" in action.tags:
        if actor.status.value == "wounded":
            adjustment += persona.weights.get("stabilize_urgency", 3.0)
        else:
            adjustment -= 5.0

    if "stress" in action.tags:
        adjustment += max(
            0, ruleset.core.stress.panic_threshold - target.stress
        ) * persona.weights.get("stress_setup", 0.15)

    if "control" in action.tags:
        existing_conditions = len(target.conditions)
        adjustment += persona.weights.get("control_setup", 0.6)
        adjustment -= existing_conditions * persona.weights.get("control_repeat_penalty", 1.2)

    if "attack" in action.tags and actor.hp > 0:
        adjustment += persona.weights.get("pressure", 0.4)

    return adjustment


def _objective_adjustment(choice: ActionChoice, state: EncounterState, persona: Persona) -> float:
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
    persona: Persona,
) -> float:
    if actor.team == runner_team:
        if choice.action_id in {"advance", "fall_back"} and choice.destination_area is not None:
            before = shortest_path_distance(state, actor.area_id, exit_area)
            after = shortest_path_distance(state, choice.destination_area, exit_area)
            if before is not None and after is not None:
                return (before - after) * persona.weights.get("objective_progress", 3.0)
        distance = shortest_path_distance(state, actor.area_id, exit_area)
        if choice.action_id not in {"advance", "fall_back"} and actor.area_id == exit_area:
            return persona.weights.get("hold_exit", 1.5)
        if (
            choice.action_id not in {"advance", "fall_back"}
            and actor.area_id != exit_area
            and not actor.engaged_with
            and distance is not None
        ):
            return -distance * persona.weights.get("objective_delay_penalty", 2.2)
        return 0.0

    target = state.actor(choice.target_id)
    if choice.action_id in {"advance", "fall_back"} and choice.destination_area is not None:
        before = shortest_path_distance(state, actor.area_id, exit_area)
        after = shortest_path_distance(state, choice.destination_area, exit_area)
        if before is not None and after is not None:
            return (before - after) * persona.weights.get("objective_intercept", 2.0)
    if target.team == runner_team:
        target_distance = shortest_path_distance(state, target.area_id, exit_area)
        if target_distance == 0:
            return persona.weights.get("deny_objective", 2.5)
        if target_distance == 1:
            return persona.weights.get("intercept_runner", 1.2)
    return 0.0


def _hold_out_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    actor: ActorState,
    hold_area: str,
    holder_team: str,
    persona: Persona,
) -> float:
    if choice.action_id in {"advance", "fall_back"} and choice.destination_area is not None:
        before = shortest_path_distance(state, actor.area_id, hold_area)
        after = shortest_path_distance(state, choice.destination_area, hold_area)
        if before is not None and after is not None:
            weight_key = (
                "objective_progress" if actor.team == holder_team else "objective_intercept"
            )
            return (before - after) * persona.weights.get(weight_key, 2.0)
    if actor.area_id == hold_area:
        return persona.weights.get("hold_ground", 1.0 if actor.team == holder_team else 0.5)
    return 0.0


def _push_adjustment(actor: ActorState, ruleset: Ruleset, persona: Persona) -> float:
    if actor.stress >= ruleset.core.stress.breakdown_threshold - 1:
        return -4.0
    if actor.stress >= ruleset.core.stress.panic_threshold:
        return persona.weights.get("panic_push_penalty", -2.0)
    return 0.0


def _has_attack_option(state: EncounterState, ruleset: Ruleset, actor_id: str) -> bool:
    from dead_by_dawn_sim.actions import legal_actions_for_actor

    return any(
        choice.action_id not in {"advance", "fall_back"}
        and "attack" in ruleset.actions[choice.action_id].tags
        for choice in legal_actions_for_actor(state, actor_id, ruleset)
    )


PERSONA_REGISTRY: dict[str, Persona] = {
    "power_gamer": Persona(
        "power_gamer",
        {
            "attack": 4.0,
            "heal": 1.0,
            "stabilize": 1.2,
            "control": 0.8,
            "stress": 0.5,
            "finisher": 2.5,
            "close_distance": 2.0,
            "pressure": 0.7,
            "heal_urgency": 0.5,
            "stabilize_urgency": 2.5,
            "objective_progress": 3.4,
            "objective_delay_penalty": 2.8,
            "hold_exit": 1.8,
        },
        1.2,
    ),
    "butt_kicker": Persona(
        "butt_kicker",
        {
            "attack": 5.0,
            "heal": 0.2,
            "stabilize": 1.5,
            "control": 0.1,
            "finisher": 1.8,
            "close_distance": 4.0,
            "pressure": 1.0,
            "panic_push_penalty": -1.5,
            "stabilize_urgency": 3.4,
            "objective_progress": 2.0,
            "objective_delay_penalty": 1.8,
            "objective_intercept": 2.3,
            "deny_objective": 2.0,
            "intercept_runner": 1.2,
        },
        1.4,
    ),
    "tactician": Persona(
        "tactician",
        {
            "attack": 2.5,
            "heal": 2.0,
            "stabilize": 2.8,
            "control": 3.0,
            "setup": 1.0,
            "finisher": 1.2,
            "close_distance": 1.4,
            "heal_urgency": 1.0,
            "rescue": 2.5,
            "control_setup": 1.0,
            "stabilize_urgency": 4.0,
            "objective_progress": 2.6,
            "objective_delay_penalty": 2.2,
            "objective_intercept": 2.6,
            "deny_objective": 2.5,
            "hold_ground": 1.5,
        },
        0.8,
    ),
    "method_actor": Persona(
        "method_actor",
        {
            "attack": 2.0,
            "heal": 2.5,
            "stabilize": 2.0,
            "control": 1.4,
            "close_distance": 0.8,
            "heal_urgency": 0.8,
            "rescue": 1.6,
            "control_setup": 0.8,
            "stabilize_urgency": 3.2,
            "low_hp_modifier": -1.0,
            "high_stress_modifier": -1.5,
            "panic_push_penalty": -3.0,
            "objective_progress": 2.4,
            "objective_delay_penalty": 1.8,
            "hold_exit": 1.2,
        },
        -0.5,
    ),
    "casual": Persona(
        "casual",
        {
            "attack": 2.4,
            "heal": 1.8,
            "stabilize": 1.5,
            "control": 0.5,
            "advance": 0.7,
            "close_distance": 1.2,
            "heal_urgency": 0.6,
            "rescue": 1.2,
            "stabilize_urgency": 2.4,
            "objective_progress": 1.6,
            "objective_delay_penalty": 1.5,
        },
        -0.2,
    ),
    "brute": Persona(
        "brute",
        {
            "attack": 4.0,
            "advance": 2.0,
            "control": 0.1,
            "finisher": 1.4,
            "close_distance": 3.0,
            "pressure": 0.8,
            "stabilize_urgency": 2.0,
            "objective_intercept": 2.8,
            "deny_objective": 3.0,
            "intercept_runner": 1.8,
        },
        0.6,
    ),
    "controller": Persona(
        "controller",
        {
            "attack": 1.2,
            "control": 4.0,
            "stress": 1.2,
            "advance": 1.0,
            "close_distance": 2.0,
            "control_setup": 1.2,
            "control_repeat_penalty": 1.8,
            "objective_intercept": 2.4,
            "deny_objective": 2.7,
            "intercept_runner": 1.6,
            "hold_ground": 1.0,
        },
        0.4,
    ),
    "panic_engine": Persona(
        "panic_engine",
        {
            "attack": 1.0,
            "stress": 4.5,
            "control": 1.0,
            "advance": 1.0,
            "close_distance": 1.0,
            "stress_setup": 0.2,
            "control_setup": 0.4,
            "control_repeat_penalty": 1.0,
            "objective_intercept": 2.0,
            "deny_objective": 2.2,
        },
        0.2,
    ),
    "finisher": Persona(
        "finisher",
        {
            "attack": 3.0,
            "finisher": 4.0,
            "control": 0.2,
            "advance": 1.0,
            "close_distance": 2.8,
            "pressure": 0.7,
            "objective_intercept": 2.6,
            "deny_objective": 3.0,
        },
        0.7,
    ),
}
