from __future__ import annotations

from dataclasses import dataclass

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.persona_logic import score_action
from dead_by_dawn_sim.rules import Ruleset
from dead_by_dawn_sim.state import EncounterState


@dataclass(frozen=True)
class Persona:
    id: str
    weights: dict[str, float]
    push_threshold: float

    def choose_action(
        self, legal_actions: list[ActionChoice], state: EncounterState, ruleset: Ruleset
    ) -> ActionChoice:
        return max(legal_actions, key=lambda choice: score_action(choice, state, ruleset, self))


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
