from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.rules import Ruleset, load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner
from dead_by_dawn_sim.state import EncounterState, synchronize_engagements, update_actor


def build_state(scenario_id: str, seed: int = 1) -> tuple[Ruleset, EncounterState]:
    ruleset = load_ruleset()
    state = EncounterRunner(ruleset).build_state(scenario_id, seed=seed)
    return ruleset, state


def actor_id_with_prefix(state: EncounterState, prefix: str) -> str:
    return next(actor_id for actor_id in state.actors if actor_id.startswith(prefix))


def actor_ids_with_prefix(state: EncounterState, prefix: str) -> list[str]:
    return [actor_id for actor_id in state.actors if actor_id.startswith(prefix)]


def update_actor_fields(state: EncounterState, actor_id: str, **changes: object) -> EncounterState:
    return update_actor(state, replace(state.actor(actor_id), **changes))


def sync_actor_update(state: EncounterState, actor_id: str, **changes: object) -> EncounterState:
    updated = update_actor_fields(state, actor_id, **changes)
    return synchronize_engagements(updated)
