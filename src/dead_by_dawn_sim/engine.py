from __future__ import annotations

from dataclasses import replace
from typing import NamedTuple

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.dice import DiceRoller
from dead_by_dawn_sim.rules import (
    ActionDefinition,
    AttackEffect,
    HealEffect,
    Ruleset,
    StressEffect,
)
from dead_by_dawn_sim.state import (
    ActorState,
    ActorStatus,
    ConditionState,
    EncounterState,
    RangeBand,
    TalentState,
    append_event,
    update_actor,
)


class RollResult(NamedTuple):
    kept: list[int]
    total: int
    is_success: bool
    is_critical: bool


def resolve_roll(
    *, raw_rolls: list[int], keep: int, modifier: int, difficulty: int, highest: bool = True
) -> RollResult:
    kept = sorted(raw_rolls, reverse=highest)[:keep]
    total = sum(kept) + modifier
    is_success = total >= difficulty
    is_critical = is_success and len(kept) >= 2 and kept[0] == kept[1]
    return RollResult(kept=kept, total=total, is_success=is_success, is_critical=is_critical)


def _effective_attack_modifier(actor: ActorState, ruleset: Ruleset) -> int:
    modifier = 0
    for condition in actor.conditions:
        modifier += ruleset.conditions[condition.id].attack_modifier
    return modifier


def _difficulty(ruleset: Ruleset, difficulty_name: str) -> int:
    return getattr(ruleset.core.difficulties, difficulty_name)


def _actor_actions_per_turn(actor: ActorState, ruleset: Ruleset) -> int:
    if actor.status in {ActorStatus.CRITICAL, ActorStatus.DEAD, ActorStatus.BROKEN}:
        return 0
    if actor.stress >= ruleset.core.stress.breakdown_threshold:
        return 0
    if actor.status is ActorStatus.WOUNDED or actor.stress >= ruleset.core.stress.panic_threshold:
        return 1
    return 2


def _decrement_conditions(actor: ActorState) -> ActorState:
    next_conditions = tuple(
        replace(condition, rounds_remaining=condition.rounds_remaining - 1)
        for condition in actor.conditions
        if condition.rounds_remaining > 1
    )
    return replace(actor, conditions=next_conditions)


def _transition_actor_state(actor: ActorState, ruleset: Ruleset) -> ActorState:
    if actor.shrouds >= ruleset.core.death.shrouds_to_die:
        return replace(actor, status=ActorStatus.DEAD)
    if actor.stress >= ruleset.core.stress.breakdown_threshold:
        return replace(actor, status=ActorStatus.BROKEN)
    if actor.hp <= 0:
        if actor.status in {ActorStatus.CRITICAL, ActorStatus.DEAD}:
            return actor
        return replace(actor, status=ActorStatus.WOUNDED, hp=0)
    return replace(actor, status=ActorStatus.NORMAL)


def _roll_check(
    *, roller: DiceRoller, ruleset: Ruleset, modifier: int, difficulty: int, push: bool
) -> RollResult:
    raw_rolls = roller.roll_d6(
        ruleset.core.check_dice + (ruleset.core.push.extra_die if push else 0)
    )
    return resolve_roll(
        raw_rolls=raw_rolls,
        keep=ruleset.core.push.keep if push else ruleset.core.keep_dice,
        modifier=modifier,
        difficulty=difficulty,
    )


def _run_stress_test(
    state: EncounterState, actor: ActorState, roller: DiceRoller, ruleset: Ruleset
) -> EncounterState:
    result = _roll_check(
        roller=roller, ruleset=ruleset, modifier=0, difficulty=actor.stress, push=False
    )
    if result.is_success:
        return append_event(state, f"{actor.actor_id} holds together under stress.")
    updated_actor = replace(actor, stress=actor.stress + 1)
    state = update_actor(state, _transition_actor_state(updated_actor, ruleset))
    return append_event(state, f"{actor.actor_id} gains stress from pushing.")


def _apply_damage(target: ActorState, amount: int, ruleset: Ruleset) -> ActorState:
    hp_after = max(target.hp - amount, 0)
    updated = replace(target, hp=hp_after)
    if (
        hp_after == 0
        and "final_girl" in target.talent_ids
        and "final_girl" not in target.talent_state.used
    ):
        updated = replace(
            updated, hp=3, talent_state=TalentState(used=target.talent_state.used | {"final_girl"})
        )
    return _transition_actor_state(updated, ruleset)


def _heal_target(target: ActorState, amount: int, ruleset: Ruleset) -> ActorState:
    healed = min(target.max_hp, target.hp + amount)
    updated = replace(target, hp=healed)
    if healed > 0 and updated.status in {ActorStatus.WOUNDED, ActorStatus.CRITICAL}:
        updated = replace(updated, status=ActorStatus.NORMAL)
    return _transition_actor_state(updated, ruleset)


def _apply_action_effect(
    state: EncounterState,
    actor: ActorState,
    target: ActorState,
    action: ActionDefinition,
    roller: DiceRoller,
    ruleset: Ruleset,
    push: bool,
) -> EncounterState:
    modifier_bonus = _effective_attack_modifier(actor, ruleset)
    effect = action.effect
    if isinstance(effect, AttackEffect):
        if actor.weapon_id is None:
            raise ValueError(f"Actor {actor.actor_id} attempted a weapon attack without a weapon.")
        weapon = ruleset.weapons[actor.weapon_id]
        modifier = actor.stats[effect.stat] + actor.skills.get(effect.skill, 0) + modifier_bonus
        result = _roll_check(
            roller=roller, ruleset=ruleset, modifier=modifier, difficulty=target.defense, push=push
        )
        if result.is_success:
            damage_roll = roller.roll_d6(1)[0]
            damage = (
                weapon.damage_die if result.is_critical else min(damage_roll, weapon.damage_die)
            )
            updated_target = _apply_damage(target, damage, ruleset)
            if "bleed" in weapon.tags:
                updated_target = replace(
                    updated_target,
                    conditions=(
                        *updated_target.conditions,
                        ConditionState(id="bleeding", rounds_remaining=3),
                    ),
                )
            state = update_actor(state, updated_target)
            state = append_event(state, f"{actor.actor_id} hits {target.actor_id} for {damage}.")
        else:
            state = append_event(state, f"{actor.actor_id} misses {target.actor_id}.")
    elif isinstance(effect, HealEffect):
        modifier = actor.stats[effect.stat] + actor.skills.get(effect.skill, 0)
        if "healing_hands" in actor.talent_ids and "healing_hands" not in actor.talent_state.used:
            result = RollResult(kept=[6, 6], total=999, is_success=True, is_critical=True)
            actor = replace(
                actor, talent_state=TalentState(used=actor.talent_state.used | {"healing_hands"})
            )
            state = update_actor(state, actor)
        else:
            result = _roll_check(
                roller=roller,
                ruleset=ruleset,
                modifier=modifier,
                difficulty=_difficulty(ruleset, effect.difficulty),
                push=push,
            )
        if result.is_success:
            amount = effect.amount + (1 if result.is_critical else 0)
            updated_target = _heal_target(target, amount, ruleset)
            state = update_actor(state, updated_target)
            state = append_event(state, f"{actor.actor_id} heals {target.actor_id} for {amount}.")
        else:
            state = append_event(state, f"{actor.actor_id} fails to heal {target.actor_id}.")
    elif isinstance(effect, StressEffect):
        modifier = actor.stats[effect.stat] + actor.skills.get(effect.skill, 0)
        result = _roll_check(
            roller=roller,
            ruleset=ruleset,
            modifier=modifier,
            difficulty=_difficulty(ruleset, effect.difficulty),
            push=push,
        )
        if result.is_success:
            updated_target = _transition_actor_state(
                replace(target, stress=target.stress + effect.amount), ruleset
            )
            state = update_actor(state, updated_target)
            state = append_event(state, f"{actor.actor_id} rattles {target.actor_id}.")
    else:
        modifier = actor.stats[effect.stat] + actor.skills.get(effect.skill, 0)
        result = _roll_check(
            roller=roller,
            ruleset=ruleset,
            modifier=modifier,
            difficulty=_difficulty(ruleset, effect.difficulty),
            push=push,
        )
        if result.is_success:
            updated_target = replace(
                target,
                conditions=(
                    *target.conditions,
                    ConditionState(id="rattled", rounds_remaining=effect.duration_rounds),
                ),
            )
            state = update_actor(state, updated_target)
            state = append_event(state, f"{actor.actor_id} rattles {target.actor_id}'s aim.")
    if push:
        state = _run_stress_test(state, state.actor(actor.actor_id), roller, ruleset)
    return state


def _advance_band(band: RangeBand) -> RangeBand:
    if band is RangeBand.FAR:
        return RangeBand.NEAR
    if band is RangeBand.NEAR:
        return RangeBand.ENGAGED
    return RangeBand.ENGAGED


def _retreat_band(band: RangeBand) -> RangeBand:
    if band is RangeBand.ENGAGED:
        return RangeBand.NEAR
    if band is RangeBand.NEAR:
        return RangeBand.FAR
    return RangeBand.FAR


def resolve_action(
    state: EncounterState, choice: ActionChoice, roller: DiceRoller, ruleset: Ruleset
) -> EncounterState:
    actor = state.actor(choice.actor_id)
    target = state.actor(choice.target_id)
    if choice.action_id == "advance":
        return append_event(
            update_actor(state, replace(actor, range_band=_advance_band(actor.range_band))),
            f"{actor.actor_id} advances.",
        )
    if choice.action_id == "fall_back":
        return append_event(
            update_actor(state, replace(actor, range_band=_retreat_band(actor.range_band))),
            f"{actor.actor_id} falls back.",
        )
    return _apply_action_effect(
        state, actor, target, ruleset.actions[choice.action_id], roller, ruleset, choice.push
    )


def start_turn(state: EncounterState, actor_id: str, ruleset: Ruleset) -> EncounterState:
    actor = state.actor(actor_id)
    damage = sum(ruleset.conditions[condition.id].damage_per_turn for condition in actor.conditions)
    if damage > 0:
        actor = _apply_damage(actor, damage, ruleset)
    actor = _decrement_conditions(actor)
    actor = _transition_actor_state(actor, ruleset)
    return update_actor(state, actor)


def end_turn(
    state: EncounterState, actor_id: str, roller: DiceRoller, ruleset: Ruleset
) -> EncounterState:
    actor = state.actor(actor_id)
    if actor.status is ActorStatus.WOUNDED:
        result = _roll_check(
            roller=roller,
            ruleset=ruleset,
            modifier=actor.stats["might"] + actor.skills.get("brace", 0),
            difficulty=_difficulty(ruleset, ruleset.core.death.wounded_to_critical_difficulty),
            push=False,
        )
        if not result.is_success:
            actor = replace(actor, status=ActorStatus.CRITICAL)
            state = append_event(
                update_actor(state, actor), f"{actor.actor_id} slips into critical condition."
            )
    elif actor.status is ActorStatus.CRITICAL:
        result = _roll_check(
            roller=roller,
            ruleset=ruleset,
            modifier=actor.stats["might"] + actor.skills.get("brace", 0),
            difficulty=_difficulty(ruleset, ruleset.core.death.critical_stabilize_difficulty),
            push=False,
        )
        if result.is_critical:
            actor = replace(actor, hp=1, status=ActorStatus.WOUNDED)
            state = append_event(update_actor(state, actor), f"{actor.actor_id} stabilizes.")
        elif not result.is_success:
            actor = _transition_actor_state(replace(actor, shrouds=actor.shrouds + 1), ruleset)
            state = append_event(update_actor(state, actor), f"{actor.actor_id} gains a shroud.")
    return state


def actions_per_turn(state: EncounterState, actor_id: str, ruleset: Ruleset) -> int:
    return _actor_actions_per_turn(state.actor(actor_id), ruleset)


def determine_winner(state: EncounterState) -> str | None:
    teams_alive: dict[str, int] = {}
    for actor in state.actors.values():
        if actor.status not in {ActorStatus.DEAD, ActorStatus.CRITICAL, ActorStatus.BROKEN}:
            teams_alive[actor.team] = teams_alive.get(actor.team, 0) + 1
    if len(teams_alive) == 1:
        return next(iter(teams_alive))
    if not teams_alive:
        return "draw"
    return None
