from __future__ import annotations

from typing import TYPE_CHECKING

from dead_by_dawn_sim.state import EncounterState, append_event

if TYPE_CHECKING:
    from dead_by_dawn_sim.action_procedure_types import (
        ActionResolutionContext,
        ProcedureResolution,
    )


def narrate_attack_hit(state: EncounterState, message: str) -> EncounterState:
    return append_event(state, message)


def narrate_attack_miss(state: EncounterState, actor_id: str, target_id: str) -> EncounterState:
    return append_event(state, f"{actor_id} misses {target_id}.")


def narrate_rattled_aim(state: EncounterState, actor_id: str, target_id: str) -> EncounterState:
    return append_event(state, f"{actor_id} rattles {target_id}'s aim.")


def _heal_message(
    before: ProcedureResolution,
    after: ProcedureResolution,
    _: bool,
) -> str:
    actor_id = before.actor.actor_id
    target_id = before.target.actor_id
    last_roll = after.last_roll
    if last_roll is None or not last_roll.is_success:
        return f"{actor_id} fails to heal {target_id}."
    healed_amount = after.target.hp - before.target.hp
    return f"{actor_id} heals {target_id} for {healed_amount}."


def _rally_message(
    before: ProcedureResolution,
    after: ProcedureResolution,
    _: bool,
) -> str:
    actor_id = before.actor.actor_id
    target_id = before.target.actor_id
    last_roll = after.last_roll
    if last_roll is None or not last_roll.is_success:
        return f"{actor_id} fails to rally {target_id}."
    return f"{actor_id} rallies {target_id}."


def _shriek_message(
    before: ProcedureResolution,
    after: ProcedureResolution,
    target_uses_stress_track: bool,
) -> str | None:
    actor_id = before.actor.actor_id
    target_id = before.target.actor_id
    last_roll = after.last_roll
    if last_roll is not None and last_roll.is_success and target_uses_stress_track:
        return f"{actor_id} rattles {target_id}."
    return None


def _trip_message(
    before: ProcedureResolution,
    after: ProcedureResolution,
    _: bool,
) -> str:
    actor_id = before.actor.actor_id
    target_id = before.target.actor_id
    last_roll = after.last_roll
    if last_roll is None or not last_roll.is_success:
        return f"{actor_id} fails to topple {target_id}."
    return f"{actor_id} puts {target_id} on the ground."


def _feint_message(
    before: ProcedureResolution,
    after: ProcedureResolution,
    _: bool,
) -> str:
    actor_id = before.actor.actor_id
    target_id = before.target.actor_id
    last_roll = after.last_roll
    if last_roll is None or not last_roll.is_success:
        return f"{actor_id} fails to topple {target_id}."
    return f"{actor_id} feints against {target_id}."


def _shove_message(
    before: ProcedureResolution,
    after: ProcedureResolution,
    _: bool,
) -> str:
    actor_id = before.actor.actor_id
    target_id = before.target.actor_id
    last_roll = after.last_roll
    if last_roll is None or not last_roll.is_success:
        return f"{actor_id} fails to shove {target_id}."
    return f"{actor_id} shoves {target_id} to {after.target.area_id}."


def _stand_up_message(
    before: ProcedureResolution,
    _: ProcedureResolution,
    __: bool,
) -> str:
    return f"{before.actor.actor_id} stands up."


NARRATION_HANDLERS = {
    "heal": _heal_message,
    "rally": _rally_message,
    "shriek": _shriek_message,
    "trip": _trip_message,
    "feint": _feint_message,
    "shove": _shove_message,
    "stand_up": _stand_up_message,
}


def narrate_procedure_action(
    ctx: ActionResolutionContext,
    before: ProcedureResolution,
    after: ProcedureResolution,
    target_uses_stress_track: bool,
) -> EncounterState:
    narration_id = ctx.action.narration_id
    if narration_id is None:
        return after.state
    handler = NARRATION_HANDLERS.get(narration_id)
    if handler is None:
        return after.state
    message = handler(before, after, target_uses_stress_track)
    if message is None:
        return after.state
    return append_event(after.state, message)
