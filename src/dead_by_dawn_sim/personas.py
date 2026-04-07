from __future__ import annotations

from dataclasses import dataclass

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.rules import Ruleset
from dead_by_dawn_sim.state import ActorState, ActorStatus, EncounterState, shortest_path_distance


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
    score += _closeout_adjustment(choice, state, ruleset, persona)

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

    if "stress" in action.tags:
        adjustment += max(
            0, ruleset.core.stress.panic_threshold - target.stress
        ) * persona.weights.get("stress_setup", 0.15)

    if "control" in action.tags:
        existing_conditions = len(target.conditions)
        adjustment += persona.weights.get("control_setup", 0.6)
        adjustment -= existing_conditions * persona.weights.get("control_repeat_penalty", 1.2)

    if choice.action_id == "grit":
        missing_hp = actor.max_hp - actor.hp
        is_bleeding = any(condition.id == "bleeding" for condition in actor.conditions)
        in_real_danger = (
            actor.status in {ActorStatus.WOUNDED, ActorStatus.CRITICAL}
            or actor.hp <= max(2, actor.max_hp // 2)
            or is_bleeding
        )
        if not in_real_danger:
            adjustment -= persona.weights.get("grit_topoff_penalty", 3.5)
        else:
            adjustment += persona.weights.get("grit_danger_bonus", 0.8)

    if choice.action_id == "rally":
        if target.actor_id == actor.actor_id:
            adjustment -= persona.weights.get("self_rally_penalty", 3.0)
        if target.engaged_with or target.weapon_id is not None:
            adjustment += persona.weights.get("ally_strike_setup", 0.8)
        if target.max_hp - target.hp > 0:
            adjustment += persona.weights.get("rally_urgency", 0.4)

    if choice.action_id == "trip":
        if any(condition.id == "prone" for condition in target.conditions):
            adjustment -= 4.0
        else:
            adjustment += persona.weights.get("trip_urgency", 0.3)

    if choice.action_id == "shove" and choice.destination_area is not None:
        if choice.destination_area != actor.area_id:
            adjustment += persona.weights.get("shove_urgency", 0.4)
        if target.area_id == actor.area_id and choice.destination_area != actor.area_id:
            adjustment += persona.weights.get("break_line", 0.6)

    if "attack" in action.tags and actor.hp > 0:
        adjustment += persona.weights.get("pressure", 0.4)

    return adjustment


def _active_enemies(state: EncounterState, team: str) -> list[ActorState]:
    return [
        candidate
        for candidate in state.actors.values()
        if candidate.team != team
        and candidate.status not in {ActorStatus.DEAD, ActorStatus.CRITICAL, ActorStatus.BROKEN}
    ]


def _closeout_adjustment(
    choice: ActionChoice, state: EncounterState, ruleset: Ruleset, persona: Persona
) -> float:
    actor = state.actor(choice.actor_id)
    enemies = _active_enemies(state, actor.team)
    if len(enemies) != 1:
        return 0.0
    last_enemy = enemies[0]
    if choice.action_id in {"advance", "fall_back"} and choice.destination_area is not None:
        before = shortest_path_distance(state, actor.area_id, last_enemy.area_id)
        after = shortest_path_distance(state, choice.destination_area, last_enemy.area_id)
        if before is not None and after is not None and after < before:
            return persona.weights.get("closeout_pursuit", 3.0) * (before - after)
        return 0.0

    action = ruleset.actions[choice.action_id]
    target = state.actor(choice.target_id)
    if target.actor_id == last_enemy.actor_id:
        if "attack" in action.tags:
            return persona.weights.get("closeout_attack", 3.5)
        if choice.action_id == "trip":
            return -persona.weights.get("closeout_trip_penalty", 3.5)
        if "control" in action.tags or "stress" in action.tags:
            return -persona.weights.get("closeout_delay", 2.0)
        return 0.0

    if "heal" in action.tags and target.status.value in {"wounded", "critical"}:
        return persona.weights.get("closeout_rescue", 1.5)
    if (
        choice.action_id == "rally"
        and target.actor_id != actor.actor_id
        and target.status.value in {"wounded", "critical"}
    ):
        return persona.weights.get("closeout_rescue", 1.0)
    if choice.action_id == "rally":
        return -persona.weights.get("closeout_rally_penalty", 4.0)
    return -persona.weights.get("closeout_delay", 2.0)


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
            "control": 0.8,
            "stress": 0.5,
            "finisher": 2.5,
            "close_distance": 2.0,
            "pressure": 0.7,
            "heal_urgency": 0.5,
            "ally_strike_setup": 1.0,
            "rally_urgency": 0.6,
            "trip_urgency": 0.2,
            "shove_urgency": 0.2,
            "objective_progress": 3.4,
            "objective_delay_penalty": 2.8,
            "hold_exit": 1.8,
            "grit_topoff_penalty": 4.5,
            "grit_danger_bonus": 0.8,
        },
        1.2,
    ),
    "butt_kicker": Persona(
        "butt_kicker",
        {
            "attack": 5.0,
            "heal": 0.2,
            "control": 0.1,
            "finisher": 1.8,
            "close_distance": 4.0,
            "pressure": 1.0,
            "panic_push_penalty": -1.5,
            "trip_urgency": 0.4,
            "shove_urgency": 0.8,
            "break_line": 0.8,
            "objective_progress": 2.0,
            "objective_delay_penalty": 1.8,
            "objective_intercept": 2.3,
            "deny_objective": 2.0,
            "intercept_runner": 1.2,
            "grit_topoff_penalty": 5.0,
            "grit_danger_bonus": 0.4,
        },
        1.4,
    ),
    "tactician": Persona(
        "tactician",
        {
            "attack": 2.5,
            "heal": 2.0,
            "control": 3.0,
            "setup": 1.0,
            "finisher": 1.2,
            "close_distance": 1.4,
            "heal_urgency": 1.0,
            "rescue": 2.5,
            "control_setup": 1.0,
            "ally_strike_setup": 2.0,
            "rally_urgency": 1.2,
            "trip_urgency": 0.2,
            "shove_urgency": 0.4,
            "objective_progress": 2.6,
            "objective_delay_penalty": 2.2,
            "objective_intercept": 2.6,
            "deny_objective": 2.5,
            "hold_ground": 1.5,
            "grit_topoff_penalty": 4.0,
            "grit_danger_bonus": 0.8,
        },
        0.8,
    ),
    "method_actor": Persona(
        "method_actor",
        {
            "attack": 2.0,
            "heal": 2.5,
            "control": 1.4,
            "close_distance": 0.8,
            "heal_urgency": 0.8,
            "rescue": 1.6,
            "control_setup": 0.8,
            "ally_strike_setup": 0.8,
            "rally_urgency": 0.5,
            "trip_urgency": 0.2,
            "low_hp_modifier": -1.0,
            "high_stress_modifier": -1.5,
            "panic_push_penalty": -3.0,
            "objective_progress": 2.4,
            "objective_delay_penalty": 1.8,
            "hold_exit": 1.2,
            "grit_topoff_penalty": 3.0,
            "grit_danger_bonus": 1.0,
        },
        -0.5,
    ),
    "casual": Persona(
        "casual",
        {
            "attack": 2.4,
            "heal": 1.8,
            "control": 0.5,
            "advance": 0.7,
            "close_distance": 1.2,
            "heal_urgency": 0.6,
            "rescue": 1.2,
            "ally_strike_setup": 0.6,
            "rally_urgency": 0.4,
            "trip_urgency": 0.1,
            "shove_urgency": 0.2,
            "objective_progress": 1.6,
            "objective_delay_penalty": 1.5,
            "grit_topoff_penalty": 3.5,
            "grit_danger_bonus": 0.6,
        },
        -0.2,
    ),
    "brute": Persona(
        "brute",
        {
            "attack": 4.4,
            "advance": 2.0,
            "control": 0.4,
            "finisher": 1.8,
            "close_distance": 3.0,
            "pressure": 0.9,
            "trip_urgency": 0.3,
            "shove_urgency": 1.0,
            "break_line": 1.0,
            "objective_intercept": 2.8,
            "deny_objective": 3.0,
            "intercept_runner": 1.8,
        },
        0.9,
    ),
    "controller": Persona(
        "controller",
        {
            "attack": 1.8,
            "control": 3.6,
            "stress": 1.2,
            "advance": 1.0,
            "close_distance": 2.0,
            "control_setup": 1.2,
            "control_repeat_penalty": 1.8,
            "trip_urgency": 0.2,
            "shove_urgency": 0.9,
            "break_line": 0.7,
            "objective_intercept": 2.4,
            "deny_objective": 2.7,
            "intercept_runner": 1.6,
            "hold_ground": 1.0,
        },
        0.6,
    ),
    "panic_engine": Persona(
        "panic_engine",
        {
            "attack": 1.4,
            "stress": 4.8,
            "control": 1.0,
            "advance": 1.0,
            "close_distance": 1.0,
            "stress_setup": 0.2,
            "control_setup": 0.4,
            "control_repeat_penalty": 1.0,
            "finisher": 0.8,
            "objective_intercept": 2.0,
            "deny_objective": 2.2,
        },
        0.4,
    ),
    "finisher": Persona(
        "finisher",
        {
            "attack": 3.6,
            "finisher": 4.8,
            "control": 0.3,
            "advance": 1.0,
            "close_distance": 2.8,
            "pressure": 0.9,
            "trip_urgency": 0.2,
            "shove_urgency": 0.5,
            "break_line": 0.4,
            "objective_intercept": 2.6,
            "deny_objective": 3.0,
        },
        0.9,
    ),
}
