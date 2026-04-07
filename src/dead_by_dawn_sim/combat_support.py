from __future__ import annotations

from dead_by_dawn_sim.rules import AttackEffect, Ruleset, WeaponDefinition
from dead_by_dawn_sim.state import ActorState


def attack_weapon(
    effect: AttackEffect, actor: ActorState, ruleset: Ruleset
) -> WeaponDefinition | None:
    weapon_id = effect.weapon_id or actor.weapon_id
    if weapon_id is None:
        return None
    return ruleset.weapons[weapon_id]


def has_condition(actor: ActorState, condition_id: str) -> bool:
    return any(condition.id == condition_id for condition in actor.conditions)
