from __future__ import annotations

from dataclasses import replace
from typing import Literal

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.combat_support import attack_weapon, has_condition
from dead_by_dawn_sim.dice import DiceRoller
from dead_by_dawn_sim.engine_rolls import (
    ContestResult,
    RollMode,
    RollResult,
    difficulty_value,
    resolve_roll,
    roll_check,
    roll_contest,
)
from dead_by_dawn_sim.engine_state import (
    actions_per_turn,
    apply_damage,
    determine_winner,
    end_turn,
    heal_target,
    remove_condition,
    run_stress_test,
    start_turn,
    transition_actor_state,
    uses_stress_track,
)
from dead_by_dawn_sim.rules import (
    ActionDefinition,
    ActionEffect,
    AttackEffect,
    BuffEffect,
    ContestConditionEffect,
    ContestDebuffEffect,
    DebuffAttackEffect,
    HealEffect,
    RemoveConditionEffect,
    Ruleset,
    StressEffect,
    WeaponDefinition,
)
from dead_by_dawn_sim.state import (
    ActorState,
    ActorStatus,
    ConditionState,
    EncounterState,
    TalentState,
    append_event,
    area_has_tag,
    can_enter_area,
    connected_area_ids,
    synchronize_engagements,
    update_actor,
)

RANGED_SKILLS = {"shoot"}

__all__ = [
    "actions_per_turn",
    "determine_winner",
    "end_turn",
    "resolve_action",
    "resolve_roll",
    "start_turn",
]


def _effective_attack_modifier(actor: ActorState, ruleset: Ruleset) -> int:
    modifier = 0
    for condition in actor.conditions:
        modifier += ruleset.conditions[condition.id].attack_modifier
    return modifier


def _spend_attack_resource(actor: ActorState, effect: AttackEffect, ruleset: Ruleset) -> ActorState:
    weapon = attack_weapon(effect, actor, ruleset)
    if weapon is None or weapon.ammo_kind is None:
        return actor
    current = actor.ammo.get(weapon.ammo_kind, 0)
    if current <= 0:
        raise ValueError(f"Actor {actor.actor_id} attempted a ranged attack without ammo.")
    next_ammo = dict(actor.ammo)
    next_ammo[weapon.ammo_kind] = current - 1
    return replace(actor, ammo=next_ammo)


def _spend_bandage(actor: ActorState) -> ActorState:
    if actor.bandages <= 0:
        raise ValueError(f"Actor {actor.actor_id} attempted first aid without bandages.")
    return replace(actor, bandages=actor.bandages - 1)


def _ranged_cover_bonus(state: EncounterState, actor: ActorState, target: ActorState) -> int:
    if actor.area_id == target.area_id:
        return 0
    return 1 if area_has_tag(state, target.area_id, "cover_rich") else 0


def _ranged_concealment_penalty(
    state: EncounterState, actor: ActorState, target: ActorState
) -> int:
    if actor.area_id == target.area_id:
        return 0
    return -1 if area_has_tag(state, target.area_id, "dark") else 0


def _roll_mode_for_action(
    actor: ActorState,
    target: ActorState,
    effect: ActionEffect,
) -> RollMode:
    swing = 0
    if isinstance(effect, AttackEffect):
        if has_condition(actor, "inspired") or has_condition(actor, "feinting"):
            swing += 1
        if has_condition(target, "prone"):
            swing += 1
    if getattr(effect, "target", None) == "enemy":
        for condition in actor.conditions:
            if condition.id != "rattled":
                continue
            if condition.source_actor_id is None or target.actor_id != condition.source_actor_id:
                swing -= 1
    if swing > 0:
        return "advantage"
    if swing < 0:
        return "disadvantage"
    return "normal"


def _consume_attack_conditions(actor: ActorState) -> ActorState:
    actor = remove_condition(actor, "inspired")
    return remove_condition(actor, "feinting")


def _mark_reaction_used(state: EncounterState, actor_id: str) -> EncounterState:
    return replace(state, used_reactions=state.used_reactions | {actor_id})


def _reaction_attack_action_id(actor: ActorState, ruleset: Ruleset) -> str | None:
    for action_id in actor.action_ids:
        action = ruleset.actions[action_id]
        if "attack" not in action.tags:
            continue
        if action.range == "engaged":
            return action_id
    return None


def _resolve_reaction_attacks(
    state: EncounterState,
    *,
    moving_actor_id: str,
    reactors: tuple[str, ...],
    roller: DiceRoller,
    ruleset: Ruleset,
) -> EncounterState:
    for reactor_id in reactors:
        if reactor_id in state.used_reactions:
            continue
        reactor = state.actor(reactor_id)
        target = state.actor(moving_actor_id)
        if reactor.status in {
            ActorStatus.CRITICAL,
            ActorStatus.STABLE,
            ActorStatus.DEAD,
            ActorStatus.BROKEN,
        }:
            continue
        reaction_action_id = _reaction_attack_action_id(reactor, ruleset)
        if reaction_action_id is None:
            continue
        action = ruleset.actions[reaction_action_id]
        effect = action.effect
        if not isinstance(effect, AttackEffect):
            continue
        modifier, difficulty = _attack_modifier_and_difficulty(
            state, reactor, target, effect, ruleset
        )
        result = roll_check(
            roller=roller,
            ruleset=ruleset,
            modifier=modifier,
            difficulty=difficulty,
            push=False,
            roll_mode=_roll_mode_for_action(reactor, target, effect),
        )
        state = _mark_reaction_used(state, reactor_id)
        if result.is_success:
            weapon = attack_weapon(effect, reactor, ruleset)
            if weapon is None:
                continue
            state = _apply_attack_hit(
                state,
                target=target,
                weapon=weapon,
                roller=roller,
                ruleset=ruleset,
                critical=result.is_critical,
                event=f"{reactor_id} reacts against {moving_actor_id} for {{damage}}.",
            )
        else:
            state = append_event(
                state, f"{reactor_id} misses a reaction attack on {moving_actor_id}."
            )
    return state


def _attack_modifier_and_difficulty(
    state: EncounterState,
    actor: ActorState,
    target: ActorState,
    effect: AttackEffect,
    ruleset: Ruleset,
) -> tuple[int, int]:
    modifier = actor.stats[effect.stat] + actor.skills.get(effect.skill, 0)
    modifier += _effective_attack_modifier(actor, ruleset)
    difficulty = target.defense
    if effect.skill in RANGED_SKILLS:
        modifier += _ranged_concealment_penalty(state, actor, target)
        difficulty += _ranged_cover_bonus(state, actor, target)
    return modifier, difficulty


def _effect_modifier(actor: ActorState, stat: Literal["might", "speed", "wits"], skill: str) -> int:
    return actor.stats[stat] + actor.skills.get(skill, 0)


def _resolve_effect_check(
    *,
    actor: ActorState,
    stat: Literal["might", "speed", "wits"],
    skill: str,
    difficulty_name: str,
    roller: DiceRoller,
    ruleset: Ruleset,
    push: bool,
    roll_mode: RollMode,
) -> RollResult:
    return roll_check(
        roller=roller,
        ruleset=ruleset,
        modifier=_effect_modifier(actor, stat, skill),
        difficulty=difficulty_value(ruleset, difficulty_name),
        push=push,
        roll_mode=roll_mode,
    )


def _resolve_effect_contest(
    *,
    actor: ActorState,
    target: ActorState,
    stat: Literal["might", "speed", "wits"],
    skill: str,
    defense_stat: Literal["might", "speed", "wits"],
    roller: DiceRoller,
    ruleset: Ruleset,
    push: bool,
    roll_mode: RollMode,
) -> ContestResult:
    return roll_contest(
        roller=roller,
        ruleset=ruleset,
        attacker_modifier=_effect_modifier(actor, stat, skill),
        defender_modifier=target.stats[defense_stat],
        push=push,
        roll_mode=roll_mode,
    )


def _append_condition(
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


def _apply_attack_hit(
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
        updated_target = _append_condition(updated_target, "bleeding", 3)
    state = update_actor(state, updated_target)
    return append_event(state, event.format(damage=damage))


def _apply_rattled(
    state: EncounterState,
    *,
    actor: ActorState,
    target: ActorState,
    duration_rounds: int,
) -> EncounterState:
    updated_target = _append_condition(
        target,
        "rattled",
        duration_rounds,
        source_actor_id=actor.actor_id,
    )
    state = update_actor(state, updated_target)
    return append_event(state, f"{actor.actor_id} rattles {target.actor_id}'s aim.")


def _move_target(
    state: EncounterState,
    target: ActorState,
    destination_area: str,
) -> EncounterState:
    moved = update_actor(state, replace(target, area_id=destination_area, engaged_with=frozenset()))
    return synchronize_engagements(moved)


def _apply_action_effect(
    state: EncounterState,
    actor: ActorState,
    target: ActorState,
    action: ActionDefinition,
    roller: DiceRoller,
    ruleset: Ruleset,
    push: bool,
    destination_area: str | None,
) -> EncounterState:
    effect = action.effect
    roll_mode = _roll_mode_for_action(actor, target, effect)
    if isinstance(effect, AttackEffect):
        weapon = attack_weapon(effect, actor, ruleset)
        if weapon is None:
            raise ValueError(f"Actor {actor.actor_id} attempted an attack without a weapon.")
        actor = _spend_attack_resource(actor, effect, ruleset) if effect.skill == "shoot" else actor
        state = update_actor(state, actor)
        modifier, difficulty = _attack_modifier_and_difficulty(
            state, actor, target, effect, ruleset
        )
        result = roll_check(
            roller=roller,
            ruleset=ruleset,
            modifier=modifier,
            difficulty=difficulty,
            push=push,
            roll_mode=roll_mode,
        )
        actor_after = _consume_attack_conditions(state.actor(actor.actor_id))
        state = update_actor(state, actor_after)
        if result.is_success:
            state = _apply_attack_hit(
                state,
                target=target,
                weapon=weapon,
                roller=roller,
                ruleset=ruleset,
                critical=result.is_critical,
                event=f"{actor.actor_id} hits {target.actor_id} for {{damage}}.",
            )
        else:
            state = append_event(state, f"{actor.actor_id} misses {target.actor_id}.")
    elif isinstance(effect, HealEffect):
        if action.id == "first_aid":
            actor = _spend_bandage(actor)
            state = update_actor(state, actor)
        modifier = actor.stats[effect.stat] + actor.skills.get(effect.skill, 0)
        if "healing_hands" in actor.talent_ids and "healing_hands" not in actor.talent_state.used:
            result = RollResult(kept=[6, 6], total=999, is_success=True, is_critical=True)
            actor = replace(
                actor,
                talent_state=TalentState(used=actor.talent_state.used | {"healing_hands"}),
            )
            state = update_actor(state, actor)
        else:
            result = roll_check(
                roller=roller,
                ruleset=ruleset,
                modifier=modifier,
                difficulty=difficulty_value(ruleset, effect.difficulty),
                push=push,
                roll_mode=roll_mode,
            )
        if result.is_success:
            amount = effect.amount + (1 if result.is_critical else 0)
            updated_target = heal_target(target, amount, ruleset)
            if action.id == "grit":
                updated_target = remove_condition(updated_target, "bleeding")
            state = update_actor(state, updated_target)
            state = append_event(state, f"{actor.actor_id} heals {target.actor_id} for {amount}.")
        else:
            state = append_event(state, f"{actor.actor_id} fails to heal {target.actor_id}.")
    elif isinstance(effect, BuffEffect):
        result = _resolve_effect_check(
            actor=actor,
            stat=effect.stat,
            skill=effect.skill,
            difficulty_name=effect.difficulty,
            roller=roller,
            ruleset=ruleset,
            push=push,
            roll_mode=roll_mode,
        )
        if result.is_success:
            updated_target = replace(
                target,
                conditions=(
                    *target.conditions,
                    ConditionState(id=effect.condition_id, rounds_remaining=effect.duration_rounds),
                ),
            )
            if result.is_critical and effect.crit_heal_amount > 0:
                updated_target = heal_target(updated_target, effect.crit_heal_amount, ruleset)
            state = update_actor(state, updated_target)
            state = append_event(state, f"{actor.actor_id} rallies {target.actor_id}.")
        else:
            state = append_event(state, f"{actor.actor_id} fails to rally {target.actor_id}.")
    elif isinstance(effect, StressEffect):
        result = _resolve_effect_check(
            actor=actor,
            stat=effect.stat,
            skill=effect.skill,
            difficulty_name=effect.difficulty,
            roller=roller,
            ruleset=ruleset,
            push=push,
            roll_mode=roll_mode,
        )
        if result.is_success and uses_stress_track(target):
            updated_target = transition_actor_state(
                replace(target, stress=target.stress + effect.amount), ruleset
            )
            state = update_actor(state, updated_target)
            state = append_event(state, f"{actor.actor_id} rattles {target.actor_id}.")
    elif isinstance(effect, DebuffAttackEffect):
        result = _resolve_effect_check(
            actor=actor,
            stat=effect.stat,
            skill=effect.skill,
            difficulty_name=effect.difficulty,
            roller=roller,
            ruleset=ruleset,
            push=push,
            roll_mode=roll_mode,
        )
        if result.is_success:
            state = _apply_rattled(
                state, actor=actor, target=target, duration_rounds=effect.duration_rounds
            )
    elif isinstance(effect, ContestDebuffEffect):
        result = _resolve_effect_contest(
            actor=actor,
            target=target,
            stat=effect.stat,
            skill=effect.skill,
            defense_stat=effect.defense_stat,
            roller=roller,
            ruleset=ruleset,
            push=push,
            roll_mode=roll_mode,
        )
        if result.is_success:
            state = _apply_rattled(
                state, actor=actor, target=target, duration_rounds=effect.duration_rounds
            )
    elif isinstance(effect, RemoveConditionEffect):
        updated_actor = remove_condition(actor, effect.condition_id)
        state = update_actor(state, updated_actor)
        state = append_event(state, f"{actor.actor_id} stands up.")
    elif isinstance(effect, ContestConditionEffect):
        result = _resolve_effect_contest(
            actor=actor,
            target=target,
            stat=effect.stat,
            skill=effect.skill,
            defense_stat=effect.defense_stat,
            roller=roller,
            ruleset=ruleset,
            push=push,
            roll_mode=roll_mode,
        )
        if result.is_success:
            recipient = actor if effect.apply_to == "self" else target
            updated_recipient = _append_condition(
                recipient,
                effect.condition_id,
                effect.duration_rounds,
            )
            state = update_actor(state, updated_recipient)
            if effect.apply_to == "self":
                state = append_event(state, f"{actor.actor_id} feints against {target.actor_id}.")
            else:
                state = append_event(
                    state, f"{actor.actor_id} puts {target.actor_id} on the ground."
                )
        else:
            state = append_event(state, f"{actor.actor_id} fails to topple {target.actor_id}.")
    else:
        if destination_area is None:
            raise ValueError(f"Action {action.id} requires a destination area.")
        if destination_area not in connected_area_ids(state, target.area_id):
            raise ValueError(
                f"Action {action.id} cannot move {target.actor_id} to {destination_area}."
            )
        if not can_enter_area(state, destination_area):
            raise ValueError(f"Action {action.id} cannot move {target.actor_id} into a full area.")
        result = _resolve_effect_contest(
            actor=actor,
            target=target,
            stat=effect.stat,
            skill=effect.skill,
            defense_stat=effect.defense_stat,
            roller=roller,
            ruleset=ruleset,
            push=push,
            roll_mode=roll_mode,
        )
        if result.is_success:
            state = _move_target(state, target, destination_area)
            moved_target = state.actor(target.actor_id)
            if result.is_critical and effect.crit_condition_id is not None:
                moved_target = replace(
                    moved_target,
                    conditions=(
                        *moved_target.conditions,
                        ConditionState(
                            id=effect.crit_condition_id,
                            rounds_remaining=effect.crit_duration_rounds,
                        ),
                    ),
                )
                state = update_actor(state, moved_target)
            state = append_event(
                state, f"{actor.actor_id} shoves {target.actor_id} to {destination_area}."
            )
        else:
            state = append_event(state, f"{actor.actor_id} fails to shove {target.actor_id}.")
    if push:
        state = run_stress_test(state, state.actor(actor.actor_id), roller, ruleset)
    return state


def _move_actor(
    state: EncounterState,
    actor: ActorState,
    destination_area: str,
    action_id: str,
    roller: DiceRoller,
    ruleset: Ruleset,
) -> EncounterState:
    reactors: tuple[str, ...] = tuple(actor.engaged_with) if action_id == "fall_back" else tuple()
    moved_state = update_actor(
        state,
        replace(actor, area_id=destination_area, engaged_with=frozenset()),
    )
    moved_state = synchronize_engagements(moved_state)
    if reactors:
        moved_state = _resolve_reaction_attacks(
            moved_state,
            moving_actor_id=actor.actor_id,
            reactors=reactors,
            roller=roller,
            ruleset=ruleset,
        )
    verb = "falls back" if action_id == "fall_back" else "advances"
    return append_event(moved_state, f"{actor.actor_id} {verb} to {destination_area}.")


def _stand_up_actor(
    state: EncounterState,
    actor: ActorState,
    action: ActionDefinition,
    roller: DiceRoller,
    ruleset: Ruleset,
) -> EncounterState:
    reactors: tuple[str, ...] = tuple(actor.engaged_with)
    if reactors:
        state = _resolve_reaction_attacks(
            state,
            moving_actor_id=actor.actor_id,
            reactors=reactors,
            roller=roller,
            ruleset=ruleset,
        )
    actor = state.actor(actor.actor_id)
    if actor.status in {
        ActorStatus.CRITICAL,
        ActorStatus.STABLE,
        ActorStatus.DEAD,
        ActorStatus.BROKEN,
    }:
        return state
    return _apply_action_effect(
        state,
        actor,
        actor,
        action,
        roller,
        ruleset,
        False,
        None,
    )


def resolve_action(
    state: EncounterState, choice: ActionChoice, roller: DiceRoller, ruleset: Ruleset
) -> EncounterState:
    actor = state.actor(choice.actor_id)
    target = state.actor(choice.target_id)
    if choice.action_id == "stand_up":
        return _stand_up_actor(state, actor, ruleset.actions[choice.action_id], roller, ruleset)
    if choice.action_id in {"advance", "fall_back"}:
        if choice.destination_area is None:
            raise ValueError(f"Movement action {choice.action_id} requires a destination area.")
        return _move_actor(state, actor, choice.destination_area, choice.action_id, roller, ruleset)
    return _apply_action_effect(
        state,
        actor,
        target,
        ruleset.actions[choice.action_id],
        roller,
        ruleset,
        choice.push,
        choice.destination_area,
    )
