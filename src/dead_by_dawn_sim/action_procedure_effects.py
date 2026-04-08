from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from dead_by_dawn_sim.action_procedure_narration import narrate_attack_hit
from dead_by_dawn_sim.engine_rolls import RollResult
from dead_by_dawn_sim.engine_state import apply_damage, mark_talent_effect_used
from dead_by_dawn_sim.state import ActorState, ConditionState, EncounterState, update_actor

if TYPE_CHECKING:
    from dead_by_dawn_sim.action_procedure_types import ActionResolutionContext
    from dead_by_dawn_sim.dice import DiceRoller
    from dead_by_dawn_sim.rules import Ruleset, TalentEffect, WeaponDefinition


def append_condition(
    target: ActorState,
    condition_id: str,
    rounds_remaining: int,
    *,
    source_actor_id: str | None = None,
) -> ActorState:
    return replace(
        target,
        conditions=(
            *target.conditions,
            ConditionState(
                id=condition_id,
                rounds_remaining=rounds_remaining,
                source_actor_id=source_actor_id,
            ),
        ),
    )


def apply_attack_hit(
    state: EncounterState,
    *,
    target: ActorState,
    weapon: WeaponDefinition,
    roller: DiceRoller,
    ruleset: Ruleset,
    critical: bool,
    event: str,
) -> EncounterState:
    damage_roll = roller.roll_d6(1)[0]
    damage = weapon.damage_die if critical else min(damage_roll, weapon.damage_die)
    updated_target = apply_damage(target, damage, ruleset)
    if "bleed" in weapon.tags:
        updated_target = append_condition(updated_target, "bleeding", 3)
    state = update_actor(state, updated_target)
    return narrate_attack_hit(state, event.format(damage=damage))


def auto_critical_heal_result(
    ctx: ActionResolutionContext, actor: ActorState, effect: TalentEffect
) -> tuple[EncounterState, ActorState, RollResult]:
    updated_actor = mark_talent_effect_used(actor, effect)
    state = update_actor(ctx.state, updated_actor)
    result = RollResult(kept=[6, 6], total=999, is_success=True, is_critical=True)
    return state, updated_actor, result
