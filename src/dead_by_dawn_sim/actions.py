from __future__ import annotations

from dataclasses import dataclass

from dead_by_dawn_sim.rules import ActionDefinition, Ruleset
from dead_by_dawn_sim.state import ActorState, EncounterState, RangeBand


@dataclass(frozen=True)
class ActionChoice:
    actor_id: str
    action_id: str
    target_id: str
    push: bool = False


def _band_value(band: RangeBand) -> int:
    return {
        RangeBand.ENGAGED: 0,
        RangeBand.NEAR: 1,
        RangeBand.FAR: 2,
    }[band]


def _can_target(
    action: ActionDefinition,
    actor: ActorState,
    target: ActorState,
    ruleset: Ruleset,
) -> bool:
    target_mode = getattr(action.effect, "target", "enemy")
    if target_mode == "ally" and actor.team != target.team:
        return False
    if target_mode == "enemy" and actor.team == target.team:
        return False
    if target_mode == "self" and actor.actor_id != target.actor_id:
        return False
    if action.range in {"self", "ally"}:
        return True
    if action.range == "enemy":
        if actor.weapon_id is not None:
            required_band = RangeBand(ruleset.weapons[actor.weapon_id].max_range)
        else:
            required_band = RangeBand.FAR
    else:
        required_band = RangeBand(action.range)
    return _band_value(actor.range_band) <= _band_value(required_band)


def legal_actions_for_actor(
    state: EncounterState,
    actor_id: str,
    ruleset: Ruleset,
) -> list[ActionChoice]:
    actor = state.actor(actor_id)
    if not actor.can_act:
        return []
    legal: list[ActionChoice] = []
    for action_id in actor.action_ids:
        action = ruleset.actions[action_id]
        for target in state.actors.values():
            if _can_target(action, actor, target, ruleset):
                legal.append(
                    ActionChoice(
                        actor_id=actor_id,
                        action_id=action_id,
                        target_id=target.actor_id,
                    )
                )
                if action.allow_push:
                    legal.append(
                        ActionChoice(
                            actor_id=actor_id,
                            action_id=action_id,
                            target_id=target.actor_id,
                            push=True,
                        )
                    )
    if actor.range_band != RangeBand.ENGAGED:
        legal.append(ActionChoice(actor_id=actor_id, action_id="advance", target_id=actor_id))
    if actor.range_band == RangeBand.ENGAGED:
        legal.append(ActionChoice(actor_id=actor_id, action_id="fall_back", target_id=actor_id))
    return legal
