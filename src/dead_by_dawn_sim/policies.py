from __future__ import annotations

from typing import Protocol

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.rules import Ruleset
from dead_by_dawn_sim.runner_types import ActorMetadata
from dead_by_dawn_sim.state import EncounterState


class ActorPolicy(Protocol):
    def choose_action(
        self, legal_actions: list[ActionChoice], state: EncounterState, ruleset: Ruleset
    ) -> ActionChoice: ...


class PolicyResolver(Protocol):
    def __call__(self, actor_id: str, metadata: ActorMetadata) -> ActorPolicy: ...


def default_policy_resolver(actor_id: str, metadata: ActorMetadata) -> ActorPolicy:
    from dead_by_dawn_sim.personas import POLICY_REGISTRY

    try:
        return POLICY_REGISTRY[metadata.policy_id]
    except KeyError as exc:
        raise KeyError(
            f"No scripted policy is registered for actor {actor_id!r} with policy_id {metadata.policy_id!r}."
        ) from exc
