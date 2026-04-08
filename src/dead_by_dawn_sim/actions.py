from __future__ import annotations

from dataclasses import dataclass

from dead_by_dawn_sim.combat_support import attack_weapon
from dead_by_dawn_sim.rules import (
    ActionDefinition,
    ActionRequirement,
    AmmoAtLeastRequirement,
    HasConditionRequirement,
    MissingHpRequirement,
    ResourceAtLeastRequirement,
    Ruleset,
    action_target_mode,
    attack_step_for_action,
    move_step_for_action,
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



def _requirement_applies(
    requirement: ActionRequirement,
    actor: ActorState,
    action: ActionDefinition,
    ruleset: Ruleset,
) -> bool:
    if isinstance(requirement, HasConditionRequirement):
        return any(condition.id == requirement.condition_id for condition in actor.conditions)
    if isinstance(requirement, MissingHpRequirement):
        return actor.hp < actor.max_hp
    if isinstance(requirement, ResourceAtLeastRequirement):
        return actor.resource_amount(requirement.resource) >= requirement.amount
    if isinstance(requirement, AmmoAtLeastRequirement):
        step = attack_step_for_action(action)
        if step is None:
            return False
        weapon = attack_weapon(step, actor, ruleset)
        if weapon is None:
            return False
        if weapon.ammo_kind is None:
            return True
        return actor.ammo.get(weapon.ammo_kind, 0) >= requirement.amount
    return bool(actor.engaged_with) is requirement.value


def _action_is_contextually_available(
    action: ActionDefinition,
    actor: ActorState,
    ruleset: Ruleset,
) -> bool:
    if not all(
        _requirement_applies(requirement, actor, action, ruleset)
        for requirement in action.availability.all_of
    ):
        return False
    return not action.availability.any_of or any(
        _requirement_applies(requirement, actor, action, ruleset)
        for requirement in action.availability.any_of
    )


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


def _action_ids_for_actor(actor: ActorState, ruleset: Ruleset) -> tuple[str, ...]:
    combined = [*actor.action_ids]
    combined.extend(
        action.id for action in ruleset.actions.values() if action.availability.universal
    )
    return tuple(dict.fromkeys(combined))


def legal_actions_for_actor(
    state: EncounterState,
    actor_id: str,
    ruleset: Ruleset,
) -> list[ActionChoice]:
    actor = state.actor(actor_id)
    if not actor.can_act:
        return []
    legal: list[ActionChoice] = []
    for action_id in _action_ids_for_actor(actor, ruleset):
        action = ruleset.actions[action_id]
        if not _action_is_contextually_available(action, actor, ruleset):
            continue
        move_step = move_step_for_action(action)
        for target in state.actors.values():
            if not _can_target(state, action, actor, target, ruleset):
                continue
            if requires_destination_choice(action):
                moved_actor = actor if move_step is not None and move_step.target == "self" else target
                destinations = [
                    area_id
                    for area_id in connected_area_ids(state, moved_actor.area_id)
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
    return legal

