from __future__ import annotations

from dataclasses import replace

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.combat_support import attack_weapon
from dead_by_dawn_sim.dice import DiceRoller
from dead_by_dawn_sim.engine_effect_handlers import (
    apply_action_effect,
    apply_attack_hit,
    attack_modifier_and_difficulty,
    roll_mode_for_action,
)
from dead_by_dawn_sim.engine_rolls import roll_check
from dead_by_dawn_sim.rules import (
    ActionDefinition,
    Ruleset,
    attack_effect_from_step,
    attack_step_for_action,
)
from dead_by_dawn_sim.state import (
    ActorState,
    ActorStatus,
    EncounterState,
    append_event,
    synchronize_engagements,
    update_actor,
)


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
        attack_step = attack_step_for_action(action)
        if attack_step is None:
            continue
        effect = attack_effect_from_step(attack_step)
        modifier, difficulty = attack_modifier_and_difficulty(
            state, reactor, target, effect, ruleset
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
            weapon = attack_weapon(effect, reactor, ruleset)
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
    return apply_action_effect(
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
    return apply_action_effect(
        state,
        actor,
        target,
        ruleset.actions[choice.action_id],
        roller,
        ruleset,
        choice.push,
        choice.destination_area,
    )
