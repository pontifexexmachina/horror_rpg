from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from dead_by_dawn_sim.combat_support import attack_weapon
from dead_by_dawn_sim.state import ActorState, update_actor

from dead_by_dawn_sim.action_procedure_steps import procedure_result_applies

if TYPE_CHECKING:
    from dead_by_dawn_sim.action_procedure_types import ProcedureResolution
    from dead_by_dawn_sim.rules import AttackRollStep, Ruleset, SpendAmmoStep, SpendResourceStep


def spend_attack_ammo(
    actor: ActorState,
    effect: AttackRollStep,
    ruleset: Ruleset,
    amount: int,
) -> ActorState:
    weapon = attack_weapon(effect, actor, ruleset)
    if weapon is None or weapon.ammo_kind is None:
        return actor
    current = actor.ammo.get(weapon.ammo_kind, 0)
    if current < amount:
        raise ValueError(f"Actor {actor.actor_id} attempted a ranged attack without enough ammo.")
    next_resources = dict(actor.resources)
    next_resources[weapon.ammo_kind] = current - amount
    return replace(actor, resources=next_resources)


def spend_resource(actor: ActorState, resource: str, amount: int) -> ActorState:
    current = actor.resource_amount(resource)
    if current < amount:
        raise ValueError(
            f"Actor {actor.actor_id} attempted to spend {amount} {resource} with only {current}."
        )
    next_resources = dict(actor.resources)
    next_resources[resource] = current - amount
    return replace(actor, resources=next_resources)


def run_spend_resource_step(
    resolution: ProcedureResolution,
    step: SpendResourceStep,
) -> ProcedureResolution:
    if not procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    actor = spend_resource(resolution.actor, step.resource, step.amount)
    state = update_actor(resolution.state, actor)
    return resolution.with_state(
        state,
        actor_id=actor.actor_id,
        target_id=resolution.target.actor_id,
    )


def run_spend_ammo_step(
    resolution: ProcedureResolution,
    action_attack_step: AttackRollStep | None,
    ruleset: Ruleset,
    step: SpendAmmoStep,
) -> ProcedureResolution:
    if not procedure_result_applies(resolution.last_roll, step.when):
        return resolution
    if action_attack_step is None:
        raise ValueError("Action cannot spend ammo without an attack step.")
    actor = spend_attack_ammo(resolution.actor, action_attack_step, ruleset, step.amount)
    state = update_actor(resolution.state, actor)
    return resolution.with_state(
        state,
        actor_id=actor.actor_id,
        target_id=resolution.target.actor_id,
    )
