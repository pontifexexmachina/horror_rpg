from __future__ import annotations

from dataclasses import dataclass
from random import Random
from typing import Literal

from dead_by_dawn_sim.actions import ActionChoice, legal_actions_for_actor
from dead_by_dawn_sim.dice import RandomDiceRoller
from dead_by_dawn_sim.engine import (
    actions_per_turn,
    determine_winner,
    end_turn,
    resolve_action,
    start_turn,
)
from dead_by_dawn_sim.personas import PERSONA_REGISTRY
from dead_by_dawn_sim.rules import Ruleset, ScenarioSideEntry
from dead_by_dawn_sim.state import (
    ActorState,
    ActorStatus,
    EncounterState,
    append_event,
    build_actor_state,
)


@dataclass(frozen=True)
class ActorMetadata:
    actor_id: str
    team: str
    name: str
    template_id: str
    persona_id: str


@dataclass(frozen=True)
class ContributionStats:
    actions_taken: int = 0
    pushes_used: int = 0
    damage_dealt: int = 0
    healing_done: int = 0
    stress_inflicted: int = 0
    control_applied: int = 0
    enemy_wounded: int = 0
    enemy_critical: int = 0
    enemy_dead: int = 0
    enemy_broken: int = 0


@dataclass(frozen=True)
class EncounterResult:
    scenario_id: str
    seed: int
    winner: str
    rounds: int
    actor_metadata: dict[str, ActorMetadata]
    actor_snapshots: dict[str, dict[str, int | str]]
    actor_contributions: dict[str, ContributionStats]
    action_counts: dict[str, int]
    push_count: int
    events: tuple[str, ...]


class EncounterRunner:
    def __init__(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset

    def build_state(self, scenario_id: str, seed: int) -> EncounterState:
        state, _ = self._build_state_bundle(scenario_id, seed)
        return state

    def _build_state_bundle(
        self, scenario_id: str, seed: int
    ) -> tuple[EncounterState, dict[str, ActorMetadata]]:
        scenario = self.ruleset.scenarios[scenario_id]
        rng = Random(seed)
        actors: dict[str, ActorState] = {}
        metadata: dict[str, ActorMetadata] = {}

        def add_side(team_label: str, entries: list[ScenarioSideEntry]) -> None:
            counter = 1
            for entry in entries:
                template = self.ruleset.actors[entry.template_id]
                persona_id = entry.persona_id or template.default_persona
                for _ in range(entry.count):
                    actor_id = f"{team_label}_{template.id}_{counter}"
                    name = f"{template.name} {counter}"
                    actors[actor_id] = build_actor_state(
                        actor_id=actor_id,
                        team=team_label,
                        template=template,
                        ruleset=self.ruleset,
                        name=name,
                    )
                    metadata[actor_id] = ActorMetadata(
                        actor_id=actor_id,
                        team=team_label,
                        name=name,
                        template_id=template.id,
                        persona_id=persona_id,
                    )
                    counter += 1

        add_side("team_a", scenario.team_a)
        add_side("team_b", scenario.team_b)
        initiative = tuple(
            actor_id
            for actor_id, _ in sorted(
                actors.items(),
                key=lambda item: (item[1].stats["speed"] + rng.randint(1, 6), item[0]),
                reverse=True,
            )
        )
        state = EncounterState(
            actors=actors,
            round_number=1,
            initiative_order=initiative,
            active_actor_id=None,
        )
        state = append_event(
            state,
            "Scenario "
            f"{scenario_id} initialized with personas "
            f"{ {actor_id: item.persona_id for actor_id, item in metadata.items()} }.",
        )
        return state, metadata

    def run(self, scenario_id: str, seed: int) -> EncounterResult:
        state, metadata = self._build_state_bundle(scenario_id, seed)
        roller = RandomDiceRoller(Random(seed))
        action_counts: dict[str, int] = {}
        contributions = {actor_id: ContributionStats() for actor_id in metadata}
        push_count = 0
        for round_number in range(1, self.ruleset.core.max_rounds + 1):
            state = EncounterState(
                actors=state.actors,
                round_number=round_number,
                initiative_order=state.initiative_order,
                active_actor_id=state.active_actor_id,
                winner=state.winner,
                events=state.events,
            )
            for actor_id in state.initiative_order:
                state = start_turn(state, actor_id, self.ruleset)
                winner = determine_winner(state)
                if winner is not None:
                    return self._finish(
                        state,
                        scenario_id,
                        seed,
                        winner,
                        round_number,
                        metadata,
                        contributions,
                        action_counts,
                        push_count,
                    )
                if not legal_actions_for_actor(state, actor_id, self.ruleset):
                    state = end_turn(state, actor_id, roller, self.ruleset)
                    continue
                persona = PERSONA_REGISTRY[metadata[actor_id].persona_id]
                for _ in range(actions_per_turn(state, actor_id, self.ruleset)):
                    legal_actions = legal_actions_for_actor(state, actor_id, self.ruleset)
                    if not legal_actions:
                        break
                    choice = persona.choose_action(legal_actions, state, self.ruleset)
                    action_counts[choice.action_id] = action_counts.get(choice.action_id, 0) + 1
                    if choice.push:
                        push_count += 1
                    previous_state = state
                    state = resolve_action(state, choice, roller, self.ruleset)
                    contributions[choice.actor_id] = self._accumulate_contribution(
                        contributions[choice.actor_id],
                        choice=choice,
                        before=previous_state,
                        after=state,
                        actor_team=metadata[choice.actor_id].team,
                    )
                    winner = determine_winner(state)
                    if winner is not None:
                        return self._finish(
                            state,
                            scenario_id,
                            seed,
                            winner,
                            round_number,
                            metadata,
                            contributions,
                            action_counts,
                            push_count,
                        )
                state = end_turn(state, actor_id, roller, self.ruleset)
                winner = determine_winner(state)
                if winner is not None:
                    return self._finish(
                        state,
                        scenario_id,
                        seed,
                        winner,
                        round_number,
                        metadata,
                        contributions,
                        action_counts,
                        push_count,
                    )
        final_winner = determine_winner(state) or "draw"
        return self._finish(
            state,
            scenario_id,
            seed,
            final_winner,
            self.ruleset.core.max_rounds,
            metadata,
            contributions,
            action_counts,
            push_count,
        )

    def _accumulate_contribution(
        self,
        current: ContributionStats,
        *,
        choice: ActionChoice,
        before: EncounterState,
        after: EncounterState,
        actor_team: str,
    ) -> ContributionStats:
        damage_dealt = 0
        healing_done = 0
        stress_inflicted = 0
        control_applied = 0
        enemy_wounded = 0
        enemy_critical = 0
        enemy_dead = 0
        enemy_broken = 0
        for actor_id, before_actor in before.actors.items():
            after_actor = after.actors[actor_id]
            if before_actor.team == actor_team:
                healing_done += max(0, after_actor.hp - before_actor.hp)
                continue
            damage_dealt += max(0, before_actor.hp - after_actor.hp)
            stress_inflicted += max(0, after_actor.stress - before_actor.stress)
            control_applied += max(0, len(after_actor.conditions) - len(before_actor.conditions))
            status_events = self._status_transition_events(before_actor, after_actor)
            enemy_wounded += status_events["wounded"]
            enemy_critical += status_events["critical"]
            enemy_dead += status_events["dead"]
            enemy_broken += status_events["broken"]
        return ContributionStats(
            actions_taken=current.actions_taken + 1,
            pushes_used=current.pushes_used + int(choice.push),
            damage_dealt=current.damage_dealt + damage_dealt,
            healing_done=current.healing_done + healing_done,
            stress_inflicted=current.stress_inflicted + stress_inflicted,
            control_applied=current.control_applied + control_applied,
            enemy_wounded=current.enemy_wounded + enemy_wounded,
            enemy_critical=current.enemy_critical + enemy_critical,
            enemy_dead=current.enemy_dead + enemy_dead,
            enemy_broken=current.enemy_broken + enemy_broken,
        )

    def _status_transition_events(
        self, before_actor: ActorState, after_actor: ActorState
    ) -> dict[Literal["wounded", "critical", "dead", "broken"], int]:
        before_rank = _status_rank(before_actor.status)
        after_rank = _status_rank(after_actor.status)
        if after_rank <= before_rank:
            return {"wounded": 0, "critical": 0, "dead": 0, "broken": 0}
        return {
            "wounded": int(before_rank < _status_rank(ActorStatus.WOUNDED) <= after_rank),
            "critical": int(before_rank < _status_rank(ActorStatus.CRITICAL) <= after_rank),
            "dead": int(before_rank < _status_rank(ActorStatus.DEAD) <= after_rank),
            "broken": int(before_rank < _status_rank(ActorStatus.BROKEN) <= after_rank),
        }

    def _finish(
        self,
        state: EncounterState,
        scenario_id: str,
        seed: int,
        winner: str,
        rounds: int,
        metadata: dict[str, ActorMetadata],
        contributions: dict[str, ContributionStats],
        action_counts: dict[str, int],
        push_count: int,
    ) -> EncounterResult:
        snapshots = {
            actor_id: {
                "hp": actor.hp,
                "status": actor.status.value,
                "stress": actor.stress,
                "shrouds": actor.shrouds,
            }
            for actor_id, actor in state.actors.items()
        }
        return EncounterResult(
            scenario_id=scenario_id,
            seed=seed,
            winner=winner,
            rounds=rounds,
            actor_metadata=metadata,
            actor_snapshots=snapshots,
            actor_contributions=contributions,
            action_counts=dict(sorted(action_counts.items())),
            push_count=push_count,
            events=state.events,
        )


def _status_rank(status: ActorStatus) -> int:
    return {
        ActorStatus.NORMAL: 0,
        ActorStatus.WOUNDED: 1,
        ActorStatus.CRITICAL: 2,
        ActorStatus.DEAD: 3,
        ActorStatus.BROKEN: 3,
    }[status]
