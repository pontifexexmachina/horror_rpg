from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import yaml

from dead_by_dawn_sim.policies import ActorPolicy
from dead_by_dawn_sim.scripted_policy_logic import score_action

if TYPE_CHECKING:
    from dead_by_dawn_sim.actions import ActionChoice
    from dead_by_dawn_sim.rules import Ruleset
    from dead_by_dawn_sim.state import EncounterState


@dataclass(frozen=True)
class ScriptedPolicy(ActorPolicy):
    id: str
    weights: dict[str, float]
    push_threshold: float

    def choose_action(
        self, legal_actions: list[ActionChoice], state: EncounterState, ruleset: Ruleset
    ) -> ActionChoice:
        return max(legal_actions, key=lambda choice: score_action(choice, state, ruleset, self))


_POLICY_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "policies" / "scripted.yml"


def _load_policy_registry() -> dict[str, ScriptedPolicy]:
    with _POLICY_DATA_PATH.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"{_POLICY_DATA_PATH} must contain a mapping of policy ids.")

    registry: dict[str, ScriptedPolicy] = {}
    for policy_id, payload in raw.items():
        if not isinstance(policy_id, str) or not isinstance(payload, dict):
            raise ValueError(f"{_POLICY_DATA_PATH} has an invalid policy entry for {policy_id!r}.")
        push_threshold = payload.get("push_threshold")
        weights = payload.get("weights")
        if not isinstance(push_threshold, int | float) or not isinstance(weights, dict):
            raise ValueError(f"{_POLICY_DATA_PATH} policy {policy_id!r} is missing valid weights.")
        if not all(isinstance(key, str) and isinstance(value, int | float) for key, value in weights.items()):
            raise ValueError(f"{_POLICY_DATA_PATH} policy {policy_id!r} has non-numeric weights.")
        registry[policy_id] = ScriptedPolicy(
            id=policy_id,
            weights={key: float(value) for key, value in weights.items()},
            push_threshold=float(push_threshold),
        )
    return registry


POLICY_REGISTRY = _load_policy_registry()
