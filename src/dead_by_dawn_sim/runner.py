from __future__ import annotations

from dataclasses import replace
from random import Random
from typing import TYPE_CHECKING

from dead_by_dawn_sim.actions import legal_actions_for_actor
from dead_by_dawn_sim.dice import RandomDiceRoller
from dead_by_dawn_sim.engine import (
    actions_per_turn,
    determine_winner,
    end_turn,
    resolve_action,
    start_turn,
)
from dead_by_dawn_sim.policies import PolicyResolver, default_policy_resolver
from dead_by_dawn_sim.runner_actions import affordable_actions, choice_action_cost, is_attack_choice
from dead_by_dawn_sim.runner_reports import accumulate_contribution, finish_encounter
from dead_by_dawn_sim.runner_state import build_state_bundle
from dead_by_dawn_sim.runner_types import ActorMetadata, ContributionStats, EncounterResult

if TYPE_CHECKING:
    from dead_by_dawn_sim.rules import Ruleset
    from dead_by_dawn_sim.state import EncounterState


class EncounterRunner:
    def __init__(
        self, ruleset: Ruleset, policy_resolver: PolicyResolver = default_policy_resolver
    ) -> None:
        self.ruleset = ruleset
        self.policy_resolver = policy_resolver

    def build_state(self, scenario_id: str, seed: int) -> EncounterState:
        state, _ = self._build_state_bundle(scenario_id, seed)
        return state

    def build_state_bundle(
        self, scenario_id: str, seed: int
    ) -> tuple[EncounterState, dict[str, ActorMetadata]]:
        return self._build_state_bundle(scenario_id, seed)

    def _build_state_bundle(
        self, scenario_id: str, seed: int
    ) -> tuple[EncounterState, dict[str, ActorMetadata]]:
        return build_state_bundle(self.ruleset, scenario_id, seed)

    def run(self, scenario_id: str, seed: int) -> EncounterResult:
        result, _ = self.run_with_final_state(scenario_id=scenario_id, seed=seed)
        return result

    def run_with_final_state(
        self,
        *,
        scenario_id: str,
        seed: int,
        state: EncounterState | None = None,
        metadata: dict[str, ActorMetadata] | None = None,
        policy_resolver: PolicyResolver | None = None,
    ) -> tuple[EncounterResult, EncounterState]:
        if state is None or metadata is None:
            state, metadata = self._build_state_bundle(scenario_id, seed)
        return self._run_state(
            scenario_id=scenario_id,
            seed=seed,
            state=state,
            metadata=metadata,
            policy_resolver=policy_resolver or self.policy_resolver,
        )

    def run_from_state(
        self,
        *,
        scenario_id: str,
        seed: int,
        state: EncounterState,
        metadata: dict[str, ActorMetadata],
        policy_resolver: PolicyResolver | None = None,
    ) -> EncounterResult:
        result, _ = self._run_state(
            scenario_id=scenario_id,
            seed=seed,
            state=state,
            metadata=metadata,
            policy_resolver=policy_resolver or self.policy_resolver,
        )
        return result

    def _finish(
        self,
        *,
        state: EncounterState,
        scenario_id: str,
        seed: int,
        winner: str,
        rounds: int,
        metadata: dict[str, ActorMetadata],
        contributions: dict[str, ContributionStats],
        action_counts: dict[str, int],
        push_count: int,
    ) -> tuple[EncounterResult, EncounterState]:
        return (
            finish_encounter(
                state,
                scenario_id=scenario_id,
                seed=seed,
                winner=winner,
                rounds=rounds,
                metadata=metadata,
                contributions=contributions,
                action_counts=action_counts,
                push_count=push_count,
            ),
            state,
        )

    def _run_state(
        self,
        *,
        scenario_id: str,
        seed: int,
        state: EncounterState,
        metadata: dict[str, ActorMetadata],
        policy_resolver: PolicyResolver,
    ) -> tuple[EncounterResult, EncounterState]:
        roller = RandomDiceRoller(Random(seed))
        action_counts: dict[str, int] = {}
        contributions = {actor_id: ContributionStats() for actor_id in metadata}
        push_count = 0
        policies = {
            actor_id: policy_resolver(actor_id, actor_metadata)
            for actor_id, actor_metadata in metadata.items()
        }
        for round_number in range(1, self.ruleset.core.max_rounds + 1):
            state = replace(
                state,
                round_number=round_number,
                used_reactions=frozenset(),
            )
            for actor_id in state.initiative_order:
                state = start_turn(state, actor_id, self.ruleset)
                winner = determine_winner(state)
                if winner is not None:
                    return self._finish(
                        state=state,
                        scenario_id=scenario_id,
                        seed=seed,
                        winner=winner,
                        rounds=round_number,
                        metadata=metadata,
                        contributions=contributions,
                        action_counts=action_counts,
                        push_count=push_count,
                    )
                if not legal_actions_for_actor(state, actor_id, self.ruleset):
                    state = end_turn(state, actor_id, roller, self.ruleset)
                    continue
                policy = policies[actor_id]
                remaining_actions = actions_per_turn(state, actor_id, self.ruleset)
                attack_used = False
                while remaining_actions > 0:
                    legal_actions = legal_actions_for_actor(state, actor_id, self.ruleset)
                    affordable = affordable_actions(legal_actions, self.ruleset, remaining_actions)
                    if attack_used:
                        affordable = [
                            choice
                            for choice in affordable
                            if not is_attack_choice(choice, self.ruleset)
                        ]
                    if not affordable:
                        break
                    choice = policy.choose_action(affordable, state, self.ruleset)
                    action_cost = choice_action_cost(choice, self.ruleset)
                    action_counts[choice.action_id] = action_counts.get(choice.action_id, 0) + 1
                    if choice.push:
                        push_count += 1
                    previous_state = state
                    state = resolve_action(state, choice, roller, self.ruleset)
                    remaining_actions -= action_cost
                    if is_attack_choice(choice, self.ruleset):
                        attack_used = True
                    contributions[choice.actor_id] = accumulate_contribution(
                        contributions[choice.actor_id],
                        choice_push=choice.push,
                        before=previous_state,
                        after=state,
                        actor_team=metadata[choice.actor_id].team,
                    )
                    winner = determine_winner(state)
                    if winner is not None:
                        return self._finish(
                            state=state,
                            scenario_id=scenario_id,
                            seed=seed,
                            winner=winner,
                            rounds=round_number,
                            metadata=metadata,
                            contributions=contributions,
                            action_counts=action_counts,
                            push_count=push_count,
                        )
                state = end_turn(state, actor_id, roller, self.ruleset)
                winner = determine_winner(state)
                if winner is not None:
                    return self._finish(
                        state=state,
                        scenario_id=scenario_id,
                        seed=seed,
                        winner=winner,
                        rounds=round_number,
                        metadata=metadata,
                        contributions=contributions,
                        action_counts=action_counts,
                        push_count=push_count,
                    )
        final_winner = determine_winner(state) or "draw"
        return self._finish(
            state=state,
            scenario_id=scenario_id,
            seed=seed,
            winner=final_winner,
            rounds=self.ruleset.core.max_rounds,
            metadata=metadata,
            contributions=contributions,
            action_counts=action_counts,
            push_count=push_count,
        )
