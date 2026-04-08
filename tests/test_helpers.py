from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.rules import Ruleset, load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner
from dead_by_dawn_sim.state import ActorState, EncounterState, synchronize_engagements, update_actor


def build_state(scenario_id: str, seed: int = 1) -> tuple[Ruleset, EncounterState]:
    ruleset = load_ruleset()
    state = EncounterRunner(ruleset).build_state(scenario_id, seed=seed)
    return ruleset, state


def actor_id_with_prefix(state: EncounterState, prefix: str) -> str:
    return next(actor_id for actor_id in state.actors if actor_id.startswith(prefix))


def actor_ids_with_prefix(state: EncounterState, prefix: str) -> list[str]:
    return [actor_id for actor_id in state.actors if actor_id.startswith(prefix)]


def _apply_resource_changes(actor: ActorState, changes: dict[str, object]) -> tuple[ActorState, dict[str, object]]:
    resource_updates = dict(actor.resources)
    remaining = dict(changes)
    ammo = remaining.pop("ammo", None)
    if isinstance(ammo, dict):
        for resource_id, amount in ammo.items():
            if not isinstance(amount, int):
                raise TypeError(f"Ammo override for {resource_id!r} must be an int.")
            resource_updates[str(resource_id)] = amount
    for resource_id in ("bandages", "medkits"):
        if resource_id in remaining:
            amount = remaining.pop(resource_id)
            if not isinstance(amount, int):
                raise TypeError(f"Resource override for {resource_id!r} must be an int.")
            resource_updates[resource_id] = amount
    if resource_updates != actor.resources:
        actor = replace(actor, resources=resource_updates)
    return actor, remaining


def update_actor_fields(state: EncounterState, actor_id: str, **changes: object) -> EncounterState:
    actor, remaining = _apply_resource_changes(state.actor(actor_id), changes)
    if remaining:
        actor = replace(actor, **remaining)
    return update_actor(state, actor)


def sync_actor_update(state: EncounterState, actor_id: str, **changes: object) -> EncounterState:
    updated = update_actor_fields(state, actor_id, **changes)
    return synchronize_engagements(updated)
