from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.action_procedure_runtime import (
    apply_action_effect,
    apply_attack_hit,
    attack_modifier_and_difficulty,
    roll_mode_for_action,
)
from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.combat_support import attack_weapon
from dead_by_dawn_sim.dice import DiceRoller
from dead_by_dawn_sim.engine_rolls import roll_check
from dead_by_dawn_sim.rules import Ruleset, attack_step_for_action
from dead_by_dawn_sim.state import (
    ActorState,
    ActorStatus,
    EncounterState,
    append_event,
)

INCAPACITATED_STATUSES = {
    ActorStatus.CRITICAL,
    ActorStatus.STABLE,
    ActorStatus.DEAD,
    ActorStatus.BROKEN,
}


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
        if reactor.status in INCAPACITATED_STATUSES:
            continue
        reaction_action_id = _reaction_attack_action_id(reactor, ruleset)
        if reaction_action_id is None:
            continue
        action = ruleset.actions[reaction_action_id]
        attack_step = attack_step_for_action(action)
        if attack_step is None:
            continue
        modifier, difficulty = attack_modifier_and_difficulty(
            state, reactor, target, attack_step, ruleset
        )
        result = roll_check(
            roller=roller,
            ruleset=ruleset,
            modifier=modifier,
            difficulty=difficulty,
            push=False,
            roll_mode=roll_mode_for_action(action, reactor, target),
        )
        state = _mark_reaction_used(state, reactor_id)
        if result.is_success:
            weapon = attack_weapon(attack_step, reactor, ruleset)
            if weapon is None:
                continue
            state = apply_attack_hit(
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


def resolve_action(
    state: EncounterState, choice: ActionChoice, roller: DiceRoller, ruleset: Ruleset
) -> EncounterState:
    action = ruleset.actions[choice.action_id]
    actor = state.actor(choice.actor_id)
    target = state.actor(choice.target_id)
    reactors = tuple(actor.engaged_with)

    if action.reaction_timing == "before" and reactors:
        state = _resolve_reaction_attacks(
            state,
            moving_actor_id=actor.actor_id,
            reactors=reactors,
            roller=roller,
            ruleset=ruleset,
        )
        actor = state.actor(choice.actor_id)
        target = state.actor(choice.target_id)
        if actor.status in INCAPACITATED_STATUSES:
            return state

    state = apply_action_effect(
        state,
        actor,
        target,
        action,
        roller,
        ruleset,
        choice.push,
        choice.destination_area,
    )

    if action.reaction_timing == "after" and reactors:
        state = _resolve_reaction_attacks(
            state,
            moving_actor_id=choice.actor_id,
            reactors=reactors,
            roller=roller,
            ruleset=ruleset,
        )
    return state
