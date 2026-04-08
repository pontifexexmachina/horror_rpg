from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.dice import DiceRoller
from dead_by_dawn_sim.engine_rolls import difficulty_value, roll_check
from dead_by_dawn_sim.rules import Ruleset, TalentEffect
from dead_by_dawn_sim.state import (
    ActorState,
    ActorStatus,
    EncounterState,
    TalentState,
    append_event,
    update_actor,
)


def uses_pc_death_track(actor: ActorState) -> bool:
    return actor.death_mode == "pc_track"


def uses_stress_track(actor: ActorState) -> bool:
    return actor.stress_mode == "track"


def talent_effect_key(effect: TalentEffect) -> str:
    return effect.key or effect.type


def talent_effect_for_actor(
    actor: ActorState, ruleset: Ruleset, effect_type: str
) -> TalentEffect | None:
    for talent_id in actor.talent_ids:
        talent = ruleset.talents.get(talent_id)
        if talent is None:
            continue
        if talent.effect.type == effect_type:
            return talent.effect
    return None


def talent_effect_used(actor: ActorState, effect: TalentEffect) -> bool:
    return talent_effect_key(effect) in actor.talent_state.used


def mark_talent_effect_used(actor: ActorState, effect: TalentEffect) -> ActorState:
    if not effect.once_per_actor:
        return actor
    effect_key = talent_effect_key(effect)
    if effect_key in actor.talent_state.used:
        return actor
    return replace(actor, talent_state=TalentState(used=actor.talent_state.used | {effect_key}))


def actor_actions_per_turn(actor: ActorState, ruleset: Ruleset) -> int:
    if actor.status in {
        ActorStatus.CRITICAL,
        ActorStatus.STABLE,
        ActorStatus.DEAD,
        ActorStatus.BROKEN,
    }:
        return 0
    if uses_stress_track(actor) and actor.stress >= ruleset.core.stress.breakdown_threshold:
        return 0
    if uses_pc_death_track(actor) and actor.status is ActorStatus.WOUNDED:
        return 1
    if uses_stress_track(actor) and actor.stress >= ruleset.core.stress.panic_threshold:
        return 1
    return 2


def decrement_conditions(actor: ActorState) -> ActorState:
    next_conditions = []
    for condition in actor.conditions:
        if condition.id == "prone":
            next_conditions.append(condition)
            continue
        if condition.rounds_remaining > 1:
            next_conditions.append(
                replace(condition, rounds_remaining=condition.rounds_remaining - 1)
            )
    return replace(actor, conditions=tuple(next_conditions))


def decrement_attack_modifiers(actor: ActorState) -> ActorState:
    next_modifiers = []
    for modifier in actor.attack_modifiers:
        if modifier.rounds_remaining > 1:
            next_modifiers.append(
                replace(modifier, rounds_remaining=modifier.rounds_remaining - 1)
            )
    return replace(actor, attack_modifiers=tuple(next_modifiers))


def remove_condition(actor: ActorState, condition_id: str) -> ActorState:
    return replace(
        actor,
        conditions=tuple(
            condition for condition in actor.conditions if condition.id != condition_id
        ),
    )


def transition_actor_state(actor: ActorState, ruleset: Ruleset) -> ActorState:
    if actor.shrouds >= ruleset.core.death.shrouds_to_die:
        return replace(actor, status=ActorStatus.DEAD)
    if uses_stress_track(actor) and actor.stress >= ruleset.core.stress.breakdown_threshold:
        return replace(actor, status=ActorStatus.BROKEN)
    if actor.hp <= 0:
        if actor.status in {ActorStatus.CRITICAL, ActorStatus.STABLE, ActorStatus.DEAD}:
            return actor
        if actor.death_mode == "die_at_zero":
            return replace(actor, status=ActorStatus.DEAD, hp=0)
        return replace(actor, status=ActorStatus.WOUNDED, hp=0)
    return replace(actor, status=ActorStatus.NORMAL)


def run_stress_test(
    state: EncounterState, actor: ActorState, roller: DiceRoller, ruleset: Ruleset
) -> EncounterState:
    if not uses_stress_track(actor):
        return state
    result = roll_check(
        roller=roller,
        ruleset=ruleset,
        modifier=0,
        difficulty=actor.stress,
        push=False,
    )
    if result.is_success:
        return append_event(state, f"{actor.actor_id} holds together under stress.")
    updated_actor = replace(actor, stress=actor.stress + 1)
    state = update_actor(state, transition_actor_state(updated_actor, ruleset))
    return append_event(state, f"{actor.actor_id} gains stress from pushing.")


def apply_damage(target: ActorState, amount: int, ruleset: Ruleset) -> ActorState:
    hp_after = max(target.hp - amount, 0)
    updated = replace(target, hp=hp_after)
    revive_effect = talent_effect_for_actor(target, ruleset, "revive_on_zero")
    if hp_after == 0 and revive_effect is not None and not talent_effect_used(target, revive_effect):
        if revive_effect.amount is None:
            raise ValueError(
                f"Talent effect {revive_effect.type} on {target.actor_id} requires an amount."
            )
        updated = replace(updated, hp=revive_effect.amount)
        updated = mark_talent_effect_used(updated, revive_effect)
    return transition_actor_state(updated, ruleset)


def heal_target(target: ActorState, amount: int, ruleset: Ruleset) -> ActorState:
    healed = min(target.max_hp, target.hp + amount)
    updated = replace(target, hp=healed)
    if healed > 0 and updated.status in {
        ActorStatus.WOUNDED,
        ActorStatus.CRITICAL,
        ActorStatus.STABLE,
    }:
        updated = replace(updated, status=ActorStatus.NORMAL)
    return transition_actor_state(updated, ruleset)


def start_turn(state: EncounterState, actor_id: str, ruleset: Ruleset) -> EncounterState:
    actor = state.actor(actor_id)
    damage = sum(ruleset.conditions[condition.id].damage_per_turn for condition in actor.conditions)
    if damage > 0:
        actor = apply_damage(actor, damage, ruleset)
    actor = transition_actor_state(actor, ruleset)
    updated_state = update_actor(state, actor)
    from dead_by_dawn_sim.state import synchronize_engagements

    return synchronize_engagements(updated_state)


def end_turn(
    state: EncounterState, actor_id: str, roller: DiceRoller, ruleset: Ruleset
) -> EncounterState:
    actor = state.actor(actor_id)
    if uses_pc_death_track(actor):
        if actor.status is ActorStatus.WOUNDED:
            result = roll_check(
                roller=roller,
                ruleset=ruleset,
                modifier=actor.stats["might"] + actor.skills.get("brace", 0),
                difficulty=difficulty_value(
                    ruleset, ruleset.core.death.wounded_to_critical_difficulty
                ),
                push=False,
            )
            if not result.is_success:
                actor = replace(actor, status=ActorStatus.CRITICAL)
                state = append_event(
                    update_actor(state, actor), f"{actor.actor_id} slips into critical condition."
                )
        elif actor.status is ActorStatus.CRITICAL:
            result = roll_check(
                roller=roller,
                ruleset=ruleset,
                modifier=actor.stats["might"] + actor.skills.get("brace", 0),
                difficulty=difficulty_value(
                    ruleset, ruleset.core.death.critical_stabilize_difficulty
                ),
                push=False,
            )
            if result.is_critical:
                actor = replace(actor, hp=0, status=ActorStatus.STABLE)
                state = append_event(update_actor(state, actor), f"{actor.actor_id} stabilizes.")
            elif not result.is_success:
                actor = transition_actor_state(replace(actor, shrouds=actor.shrouds + 1), ruleset)
                state = append_event(
                    update_actor(state, actor), f"{actor.actor_id} gains a shroud."
                )
    actor = decrement_conditions(actor)
    actor = decrement_attack_modifiers(actor)
    state = update_actor(state, actor)
    from dead_by_dawn_sim.state import synchronize_engagements

    return synchronize_engagements(state)


def actions_per_turn(state: EncounterState, actor_id: str, ruleset: Ruleset) -> int:
    return actor_actions_per_turn(state.actor(actor_id), ruleset)


def determine_winner(state: EncounterState) -> str | None:
    if state.objective.type == "reach_exit" and state.objective.area_id is not None:
        team = state.objective.team
        escaping = [
            actor
            for actor in state.actors.values()
            if actor.team == team and actor.status is not ActorStatus.DEAD
        ]
        if escaping and all(actor.area_id == state.objective.area_id for actor in escaping):
            return team
    teams_alive: dict[str, int] = {}
    for actor in state.actors.values():
        if actor.status not in {
            ActorStatus.DEAD,
            ActorStatus.CRITICAL,
            ActorStatus.STABLE,
            ActorStatus.BROKEN,
        }:
            teams_alive[actor.team] = teams_alive.get(actor.team, 0) + 1
    if len(teams_alive) == 1:
        return next(iter(teams_alive))
    if not teams_alive:
        return "draw"
    return None
