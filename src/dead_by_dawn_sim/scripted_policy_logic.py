from __future__ import annotations

from typing import Protocol

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.rules import Ruleset
from dead_by_dawn_sim.scripted_policy_objectives import closeout_adjustment, objective_adjustment
from dead_by_dawn_sim.state import ActorState, ActorStatus, EncounterState


class ScoredPolicy(Protocol):
    @property
    def weights(self) -> dict[str, float]: ...

    @property
    def push_threshold(self) -> float: ...


def score_action(
    choice: ActionChoice, state: EncounterState, ruleset: Ruleset, policy: ScoredPolicy
) -> float:
    actor = state.actor(choice.actor_id)
    target = state.actor(choice.target_id)
    score = _base_action_score(choice, state, ruleset, policy, actor, target)
    score += objective_adjustment(choice, state, policy)
    score += closeout_adjustment(choice, state, ruleset, policy)
    score += _actor_state_adjustment(actor, ruleset, policy)
    return score


def _base_action_score(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    policy: ScoredPolicy,
    actor: ActorState,
    target: ActorState,
) -> float:
    if choice.action_id in {"advance", "fall_back"}:
        return _movement_action_score(choice, state, ruleset, policy, actor)
    if choice.action_id == "stand_up":
        score = policy.weights.get("stand_up", 1.5)
        if actor.engaged_with:
            score += policy.weights.get("stand_up_urgency", 1.0)
        return score

    action = ruleset.actions[choice.action_id]
    score = sum(policy.weights.get(tag, 0.0) for tag in action.tags)
    if target.hp <= max(2, target.max_hp // 3):
        score += policy.weights.get("finisher", 0.0)
    score += _context_adjustment(choice, state, ruleset, policy, actor, target)
    if choice.push:
        score += policy.push_threshold
        score += _push_adjustment(actor, ruleset, policy)
    return score


def _movement_action_score(
    choice: ActionChoice,
    state: EncounterState,
    ruleset: Ruleset,
    policy: ScoredPolicy,
    actor: ActorState,
) -> float:
    score = policy.weights.get(choice.action_id, 0.0)
    if choice.action_id == "advance" and not _has_attack_option(state, ruleset, choice.actor_id):
        score += policy.weights.get("close_distance", 0.0)
    if choice.action_id == "fall_back" and actor.hp <= max(2, actor.max_hp // 3):
        score += policy.weights.get("escape", 0.0)
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
    actor: ActorState,
    target: ActorState,
) -> float:
    action = ruleset.actions[choice.action_id]
    adjustment = 0.0
    adjustment += _heal_context_adjustment(action.tags, target, policy)
    adjustment += _stress_context_adjustment(action.tags, target, ruleset, policy)
    adjustment += _control_context_adjustment(action.tags, target, policy)
    adjustment += _grit_context_adjustment(choice, actor, policy)
    adjustment += _rally_context_adjustment(choice, actor, target, policy)
    adjustment += _trip_context_adjustment(choice, state, actor, target, policy)
    adjustment += _shove_context_adjustment(choice, actor, target, policy)
    if "attack" in action.tags and actor.hp > 0:
        adjustment += policy.weights.get("pressure", 0.4)
    return adjustment


def _heal_context_adjustment(
    action_tags: list[str], target: ActorState, policy: ScoredPolicy
) -> float:
    if "heal" not in action_tags:
        return 0.0
    missing_hp = target.max_hp - target.hp
    adjustment = -4.0 if missing_hp == 0 else missing_hp * policy.weights.get("heal_urgency", 0.2)
    if target.status.value in {"wounded", "critical"}:
        adjustment += policy.weights.get("rescue", 0.5)
    return adjustment


def _stress_context_adjustment(
    action_tags: list[str], target: ActorState, ruleset: Ruleset, policy: ScoredPolicy
) -> float:
    if "stress" not in action_tags:
        return 0.0
    headroom = max(0, ruleset.core.stress.panic_threshold - target.stress)
    return headroom * policy.weights.get("stress_setup", 0.15)


def _control_context_adjustment(
    action_tags: list[str], target: ActorState, policy: ScoredPolicy
) -> float:
    if "control" not in action_tags:
        return 0.0
    existing_conditions = len(target.conditions)
    adjustment = policy.weights.get("control_setup", 0.6)
    adjustment -= existing_conditions * policy.weights.get("control_repeat_penalty", 1.2)
    return adjustment


def _grit_context_adjustment(
    choice: ActionChoice, actor: ActorState, policy: ScoredPolicy
) -> float:
    if choice.action_id != "grit":
        return 0.0
    is_bleeding = any(condition.id == "bleeding" for condition in actor.conditions)
    in_real_danger = (
        actor.status in {ActorStatus.WOUNDED, ActorStatus.CRITICAL}
        or actor.hp <= max(2, actor.max_hp // 2)
        or is_bleeding
    )
    if not in_real_danger:
        return -policy.weights.get("grit_topoff_penalty", 3.5)
    return policy.weights.get("grit_danger_bonus", 0.8)


def _rally_context_adjustment(
    choice: ActionChoice, actor: ActorState, target: ActorState, policy: ScoredPolicy
) -> float:
    if choice.action_id != "rally":
        return 0.0
    adjustment = 0.0
    if target.actor_id == actor.actor_id:
        adjustment -= policy.weights.get("self_rally_penalty", 3.0)
    if target.engaged_with or target.weapon_id is not None:
        adjustment += policy.weights.get("ally_strike_setup", 0.8)
    if target.max_hp - target.hp > 0:
        adjustment += policy.weights.get("rally_urgency", 0.4)
    return adjustment


def _trip_context_adjustment(
    choice: ActionChoice,
    state: EncounterState,
    actor: ActorState,
    target: ActorState,
    policy: ScoredPolicy,
) -> float:
    if choice.action_id != "trip":
        return 0.0
    if any(condition.id == "prone" for condition in target.conditions):
        return -4.0
    active_allies_in_area = sum(
        1
        for candidate in state.actors.values()
        if candidate.team == actor.team
        and candidate.area_id == actor.area_id
        and candidate.status
        not in {
            ActorStatus.DEAD,
            ActorStatus.CRITICAL,
            ActorStatus.STABLE,
            ActorStatus.BROKEN,
        }
    )
    adjustment = -policy.weights.get("trip_baseline_penalty", 2.5)
    adjustment += max(0, active_allies_in_area - 1) * policy.weights.get(
        "trip_teamwork_bonus", 0.4
    )
    if target.hp <= max(2, target.max_hp // 2):
        adjustment -= policy.weights.get("trip_finish_penalty", 1.5)
    else:
        adjustment += policy.weights.get("trip_urgency", 0.3)
    if actor.hp <= max(2, actor.max_hp // 3):
        adjustment -= policy.weights.get("trip_risk_penalty", 0.8)
    return adjustment


def _shove_context_adjustment(
    choice: ActionChoice, actor: ActorState, target: ActorState, policy: ScoredPolicy
) -> float:
    if choice.action_id != "shove" or choice.destination_area is None:
        return 0.0
    adjustment = 0.0
    if choice.destination_area != actor.area_id:
        adjustment += policy.weights.get("shove_urgency", 0.4)
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
        choice.action_id not in {"advance", "fall_back", "stand_up"}
        and "attack" in ruleset.actions[choice.action_id].tags
        for choice in legal_actions_for_actor(state, actor_id, ruleset)
    )

