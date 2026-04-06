from __future__ import annotations

from dataclasses import dataclass

from dead_by_dawn_sim.actions import ActionChoice
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
        return max(legal_actions, key=lambda choice: _score_action(choice, state, ruleset, self))


def _score_action(
    choice: ActionChoice, state: EncounterState, ruleset: Ruleset, persona: Persona
) -> float:
    score = 0.0
    if choice.action_id in {"advance", "fall_back"}:
        score += persona.weights.get(choice.action_id, 0.0)
    else:
        action = ruleset.actions[choice.action_id]
        for tag in action.tags:
            score += persona.weights.get(tag, 0.0)
        target = state.actor(choice.target_id)
        if target.hp <= max(2, target.max_hp // 3):
            score += persona.weights.get("finisher", 0.0)
        if choice.push:
            score += persona.push_threshold
    actor = state.actor(choice.actor_id)
    if actor.hp <= max(2, actor.max_hp // 3):
        score += persona.weights.get("low_hp_modifier", 0.0)
    if actor.stress >= ruleset.core.stress.panic_threshold:
        score += persona.weights.get("high_stress_modifier", 0.0)
    return score


PERSONA_REGISTRY: dict[str, Persona] = {
    "power_gamer": Persona(
        "power_gamer",
        {"attack": 4.0, "heal": 1.0, "control": 0.8, "stress": 0.5, "finisher": 2.5},
        1.2,
    ),
    "butt_kicker": Persona(
        "butt_kicker", {"attack": 5.0, "heal": 0.2, "control": 0.1, "finisher": 1.8}, 1.4
    ),
    "tactician": Persona(
        "tactician",
        {"attack": 2.5, "heal": 2.0, "control": 3.0, "setup": 1.0, "finisher": 1.2},
        0.8,
    ),
    "method_actor": Persona(
        "method_actor",
        {
            "attack": 2.0,
            "heal": 2.5,
            "control": 1.4,
            "low_hp_modifier": -1.0,
            "high_stress_modifier": -1.5,
        },
        -0.5,
    ),
    "casual": Persona("casual", {"attack": 2.4, "heal": 1.8, "control": 0.5, "advance": 0.7}, -0.2),
    "brute": Persona(
        "brute", {"attack": 4.0, "advance": 2.0, "control": 0.1, "finisher": 1.4}, 0.6
    ),
    "controller": Persona(
        "controller", {"attack": 1.2, "control": 4.0, "stress": 1.2, "advance": 1.0}, 0.4
    ),
    "panic_engine": Persona(
        "panic_engine", {"attack": 1.0, "stress": 4.5, "control": 1.0, "advance": 1.0}, 0.2
    ),
    "finisher": Persona(
        "finisher", {"attack": 3.0, "finisher": 4.0, "control": 0.2, "advance": 1.0}, 0.7
    ),
}
