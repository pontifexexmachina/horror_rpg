from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from dead_by_dawn_sim.rules import (
    ActionDefinition,
    Ruleset,
    action_has_behavior,
    action_is_attack,
    action_is_control,
    action_is_heal,
    action_is_movement,
    action_is_stress,
)
from dead_by_dawn_sim.scripted_policy_objectives import closeout_adjustment, objective_adjustment
from dead_by_dawn_sim.state import ActorState, ActorStatus, EncounterState

if TYPE_CHECKING:
    from dead_by_dawn_sim.actions import ActionChoice


class ScoredPolicy(Protocol):
    @property
    def weights(self) -> dict[str, float]: ...

    @property
    def push_threshold(self) -> float: ...


_INACTIVE = {ActorStatus.DEAD, ActorStatus.CRITICAL, ActorStatus.STABLE, ActorStatus.BROKEN}


def score_action(
    choice: ActionChoice, state: EncounterState, ruleset: Ruleset, policy: ScoredPolicy
) -> float:
    actor = state.actor(choice.actor_id)
    target = state.actor(choice.target_id)
    return (
        _base_action_score(choice, state, ruleset, policy, actor, target)
        + objective_adjustment(choice, state, ruleset, policy)
        + closeout_adjustment(choice, state, ruleset, policy)
        + _actor_state_adjustment(actor, ruleset, policy)
    )


def _tag_score(action: ActionDefinition, policy: ScoredPolicy) -> float:
    return sum(policy.weights.get(tag, 0.0) for tag in action.tags)


def _base_action_score(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    policy: ScoredPolicy,
    actor: ActorState,
    target: ActorState,
) -> float:
    action = ruleset.actions[choice.action_id]
    if action_is_movement(action):
        score = _tag_score(action, policy)
        if action_has_behavior(action, "approach") and not _has_attack_option(state, ruleset, choice.actor_id):
            score += policy.weights.get("close_distance", 0.0)
        if action_has_behavior(action, "retreat") and actor.hp <= max(2, actor.max_hp // 3):
            score += policy.weights.get("escape", 0.0)
        return score
    if action_has_behavior(action, "stand_up"):
        return policy.weights.get("stand_up", 1.5) + (
            policy.weights.get("stand_up_urgency", 1.0) if actor.engaged_with else 0.0
        )

    score = _tag_score(action, policy)
    if target.hp <= max(2, target.max_hp // 3):
        score += policy.weights.get("finisher", 0.0)
    score += _context_adjustment(choice, state, ruleset, policy, action, actor, target)
    if choice.push:
        return score + policy.push_threshold + _push_adjustment(actor, ruleset, policy)
    return score


def _actor_state_adjustment(actor: ActorState, ruleset: Ruleset, policy: ScoredPolicy) -> float:
    adjustment = 0.0
    if actor.hp <= max(2, actor.max_hp // 3):
        adjustment += policy.weights.get("low_hp_modifier", 0.0)
    if actor.stress >= ruleset.core.stress.panic_threshold:
        adjustment += policy.weights.get("high_stress_modifier", 0.0)
    return adjustment


def _context_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    policy: ScoredPolicy,
    action: ActionDefinition,
    actor: ActorState,
    target: ActorState,
) -> float:
    adjustment = sum(
        scorer(action, target, policy)
        for scorer in (_heal_context_adjustment, _control_context_adjustment)
    )
    adjustment += _stress_context_adjustment(action, target, ruleset, policy)
    adjustment += _grit_context_adjustment(choice, action, actor, policy)
    adjustment += _rally_context_adjustment(action, actor, target, policy)
    adjustment += _trip_context_adjustment(action, state, actor, target, policy)
    adjustment += _shove_context_adjustment(choice, action, actor, target, policy)
    if action_is_attack(action) and actor.hp > 0:
        adjustment += policy.weights.get("pressure", 0.4)
    return adjustment


def _heal_context_adjustment(
    action: ActionDefinition,
    target: ActorState,
    policy: ScoredPolicy,
) -> float:
    if not action_is_heal(action):
        return 0.0
    missing_hp = target.max_hp - target.hp
    return (-4.0 if missing_hp == 0 else missing_hp * policy.weights.get("heal_urgency", 0.2)) + (
        policy.weights.get("rescue", 0.5) if target.status.value in {"wounded", "critical"} else 0.0
    )


def _stress_context_adjustment(
    action: ActionDefinition,
    target: ActorState,
    ruleset: Ruleset,
    policy: ScoredPolicy,
) -> float:
    if not action_is_stress(action):
        return 0.0
    headroom = max(0, ruleset.core.stress.panic_threshold - target.stress)
    return headroom * policy.weights.get("stress_setup", 0.15)


def _control_context_adjustment(
    action: ActionDefinition,
    target: ActorState,
    policy: ScoredPolicy,
) -> float:
    if not action_is_control(action):
        return 0.0
    return policy.weights.get("control_setup", 0.6) - len(target.conditions) * policy.weights.get(
        "control_repeat_penalty", 1.2
    )


def _grit_context_adjustment(
    choice: ActionChoice,
    action: ActionDefinition,
    actor: ActorState,
    policy: ScoredPolicy,
) -> float:
    if not action_has_behavior(action, "self_heal") or choice.target_id != choice.actor_id:
        return 0.0
    in_real_danger = (
        actor.status in {ActorStatus.WOUNDED, ActorStatus.CRITICAL}
        or actor.hp <= max(2, actor.max_hp // 2)
        or any(condition.id == "bleeding" for condition in actor.conditions)
    )
    if in_real_danger:
        return policy.weights.get("grit_danger_bonus", 0.8)
    return -policy.weights.get("grit_topoff_penalty", 3.5)


def _rally_context_adjustment(
    action: ActionDefinition,
    actor: ActorState,
    target: ActorState,
    policy: ScoredPolicy,
) -> float:
    if not action_has_behavior(action, "ally_support"):
        return 0.0
    return (
        (-policy.weights.get("self_rally_penalty", 3.0) if target.actor_id == actor.actor_id else 0.0)
        + (policy.weights.get("ally_strike_setup", 0.8) if target.engaged_with or target.weapon_id is not None else 0.0)
        + (policy.weights.get("rally_urgency", 0.4) if target.max_hp - target.hp > 0 else 0.0)
    )


def _trip_context_adjustment(
    action: ActionDefinition,
    state: EncounterState,
    actor: ActorState,
    target: ActorState,
    policy: ScoredPolicy,
) -> float:
    if not action_has_behavior(action, "control_setup"):
        return 0.0
    if any(condition.id == "prone" for condition in target.conditions):
        return -4.0
    active_allies_in_area = sum(
        1
        for candidate in state.actors.values()
        if candidate.team == actor.team
        and candidate.area_id == actor.area_id
        and candidate.status not in _INACTIVE
    )
    adjustment = -policy.weights.get("trip_baseline_penalty", 2.5)
    adjustment += max(0, active_allies_in_area - 1) * policy.weights.get("trip_teamwork_bonus", 0.4)
    adjustment += (
        -policy.weights.get("trip_finish_penalty", 1.5)
        if target.hp <= max(2, target.max_hp // 2)
        else policy.weights.get("trip_urgency", 0.3)
    )
    if actor.hp <= max(2, actor.max_hp // 3):
        adjustment -= policy.weights.get("trip_risk_penalty", 0.8)
    return adjustment


def _shove_context_adjustment(
    choice: ActionChoice,
    action: ActionDefinition,
    actor: ActorState,
    target: ActorState,
    policy: ScoredPolicy,
) -> float:
    if not action_has_behavior(action, "control_reposition") or choice.destination_area is None:
        return 0.0
    adjustment = policy.weights.get("shove_urgency", 0.4) if choice.destination_area != actor.area_id else 0.0
    if target.area_id == actor.area_id and choice.destination_area != actor.area_id:
        adjustment += policy.weights.get("break_line", 0.6)
    return adjustment


def _push_adjustment(actor: ActorState, ruleset: Ruleset, policy: ScoredPolicy) -> float:
    if actor.stress >= ruleset.core.stress.breakdown_threshold - 1:
        return -4.0
    if actor.stress >= ruleset.core.stress.panic_threshold:
        return policy.weights.get("panic_push_penalty", -2.0)
    return 0.0


def _has_attack_option(state: EncounterState, ruleset: Ruleset, actor_id: str) -> bool:
    from dead_by_dawn_sim.actions import legal_actions_for_actor

    return any(
        action_is_attack(ruleset.actions[choice.action_id])
        for choice in legal_actions_for_actor(state, actor_id, ruleset)
    )
