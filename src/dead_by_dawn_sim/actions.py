from __future__ import annotations

from dataclasses import dataclass

from dead_by_dawn_sim.combat_support import attack_weapon, has_condition
from dead_by_dawn_sim.rules import (
    ActionDefinition,
    Ruleset,
    action_target_mode,
    attack_step_for_action,
    requires_destination_choice,
)
from dead_by_dawn_sim.state import (
    ActorState,
    EncounterState,
    can_enter_area,
    connected_area_ids,
    has_line_of_sight,
)


@dataclass(frozen=True)
class ActionChoice:
    actor_id: str
    action_id: str
    target_id: str
    push: bool = False
    destination_area: str | None = None


def _has_ammo_for_attack(actor: ActorState, attack: ActionDefinition, ruleset: Ruleset) -> bool:
    step = attack_step_for_action(attack)
    if step is None:
        return False
    weapon = attack_weapon(step, actor, ruleset)
    if weapon is None:
        return False
    if weapon.ammo_kind is None:
        return True
    return actor.ammo.get(weapon.ammo_kind, 0) > 0


def _action_is_contextually_available(
    action: ActionDefinition,
    actor: ActorState,
    ruleset: Ruleset,
) -> bool:
    attack_step = attack_step_for_action(action)
    if attack_step is not None and attack_step.skill == "shoot":
        return _has_ammo_for_attack(actor, action, ruleset)
    if action.id == "first_aid":
        return actor.bandages > 0
    if action.id == "grit":
        is_bleeding = any(condition.id == "bleeding" for condition in actor.conditions)
        return actor.hp < actor.max_hp or is_bleeding
    return True


def _is_same_area(actor: ActorState, target: ActorState) -> bool:
    return actor.area_id == target.area_id


def _is_connected_target(state: EncounterState, actor: ActorState, target: ActorState) -> bool:
    return has_line_of_sight(state, actor.area_id, target.area_id)


def _can_target(
    state: EncounterState,
    action: ActionDefinition,
    actor: ActorState,
    target: ActorState,
    ruleset: Ruleset,
) -> bool:
    target_mode = action_target_mode(action)
    if target_mode == "ally" and actor.team != target.team:
        return False
    if target_mode == "enemy" and actor.team == target.team:
        return False
    if target_mode == "self" and actor.actor_id != target.actor_id:
        return False
    if action.range == "self":
        return actor.actor_id == target.actor_id
    if action.range == "ally":
        return actor.team == target.team and _is_same_area(actor, target)
    if action.range == "engaged":
        return target.actor_id in actor.engaged_with
    if action.range == "near":
        return _is_same_area(actor, target)
    if action.range == "far":
        return _is_same_area(actor, target) or _is_connected_target(state, actor, target)
    if action.range == "enemy":
        attack_step = attack_step_for_action(action)
        if attack_step is not None:
            weapon = attack_weapon(attack_step, actor, ruleset)
            if weapon is None:
                return False
            if weapon.max_range == "engaged":
                return target.actor_id in actor.engaged_with
            if weapon.max_range == "near":
                return _is_same_area(actor, target)
        return _is_same_area(actor, target) or _is_connected_target(state, actor, target)
    return False


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
        if not _action_is_contextually_available(action, actor, ruleset):
            continue
        for target in state.actors.values():
            if not _can_target(state, action, actor, target, ruleset):
                continue
            if requires_destination_choice(action):
                destinations = [
                    area_id
                    for area_id in connected_area_ids(state, target.area_id)
                    if can_enter_area(state, area_id)
                ]
                for destination_area in destinations:
                    legal.append(
                        ActionChoice(
                            actor_id=actor_id,
                            action_id=action_id,
                            target_id=target.actor_id,
                            destination_area=destination_area,
                        )
                    )
                    if action.allow_push:
                        legal.append(
                            ActionChoice(
                                actor_id=actor_id,
                                action_id=action_id,
                                target_id=target.actor_id,
                                push=True,
                                destination_area=destination_area,
                            )
                        )
                continue
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
    if has_condition(actor, "prone") and "stand_up" in ruleset.actions:
        legal.append(
            ActionChoice(
                actor_id=actor_id,
                action_id="stand_up",
                target_id=actor_id,
            )
        )

    move_targets = [
        area_id
        for area_id in connected_area_ids(state, actor.area_id)
        if can_enter_area(state, area_id)
    ]
    if actor.engaged_with:
        for destination_area in move_targets:
            legal.append(
                ActionChoice(
                    actor_id=actor_id,
                    action_id="fall_back",
                    target_id=actor_id,
                    destination_area=destination_area,
                )
            )
    else:
        for destination_area in move_targets:
            legal.append(
                ActionChoice(
                    actor_id=actor_id,
                    action_id="advance",
                    target_id=actor_id,
                    destination_area=destination_area,
                )
            )
    return legal
