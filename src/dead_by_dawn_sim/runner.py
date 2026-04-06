from __future__ import annotations

from dataclasses import dataclass
from random import Random

from dead_by_dawn_sim.actions import legal_actions_for_actor
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
from dead_by_dawn_sim.state import EncounterState, append_event, build_actor_state


@dataclass(frozen=True)
class EncounterResult:
    scenario_id: str
    seed: int
    winner: str
    rounds: int
    actor_snapshots: dict[str, dict[str, int | str]]
    events: tuple[str, ...]


class EncounterRunner:
    def __init__(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset

    def build_state(self, scenario_id: str, seed: int) -> EncounterState:
        scenario = self.ruleset.scenarios[scenario_id]
        rng = Random(seed)
        actors = {}
        persona_map = {}

        def add_side(team_label: str, entries: list[ScenarioSideEntry]) -> None:
            counter = 1
            for entry in entries:
                template = self.ruleset.actors[entry.template_id]
                persona_id = entry.persona_id or template.default_persona
                for _ in range(entry.count):
                    actor_id = f"{team_label}_{template.id}_{counter}"
                    actors[actor_id] = build_actor_state(
                        actor_id=actor_id,
                        team=team_label,
                        template=template,
                        ruleset=self.ruleset,
                        name=f"{template.name} {counter}",
                    )
                    persona_map[actor_id] = persona_id
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
        return append_event(
            state,
            f"Scenario {scenario_id} initialized with personas {persona_map}.",
        )

    def run(self, scenario_id: str, seed: int) -> EncounterResult:
        state = self.build_state(scenario_id, seed)
        roller = RandomDiceRoller(Random(seed))
        scenario = self.ruleset.scenarios[scenario_id]
        persona_map: dict[str, str] = {}
        for actor_id, actor in state.actors.items():
            template = self.ruleset.actors[actor.template_id]
            persona_map[actor_id] = next(
                (
                    entry.persona_id
                    for entry in (scenario.team_a + scenario.team_b)
                    if entry.template_id == template.id and entry.persona_id is not None
                ),
                template.default_persona,
            )
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
                    return self._finish(state, scenario_id, seed, winner, round_number)
                if not legal_actions_for_actor(state, actor_id, self.ruleset):
                    state = end_turn(state, actor_id, roller, self.ruleset)
                    continue
                persona = PERSONA_REGISTRY[persona_map[actor_id]]
                for _ in range(actions_per_turn(state, actor_id, self.ruleset)):
                    legal_actions = legal_actions_for_actor(state, actor_id, self.ruleset)
                    if not legal_actions:
                        break
                    choice = persona.choose_action(legal_actions, state, self.ruleset)
                    state = resolve_action(state, choice, roller, self.ruleset)
                    winner = determine_winner(state)
                    if winner is not None:
                        return self._finish(state, scenario_id, seed, winner, round_number)
                state = end_turn(state, actor_id, roller, self.ruleset)
                winner = determine_winner(state)
                if winner is not None:
                    return self._finish(state, scenario_id, seed, winner, round_number)
        final_winner = determine_winner(state) or "draw"
        return self._finish(
            state,
            scenario_id,
            seed,
            final_winner,
            self.ruleset.core.max_rounds,
        )

    def _finish(
        self,
        state: EncounterState,
        scenario_id: str,
        seed: int,
        winner: str,
        rounds: int,
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
            actor_snapshots=snapshots,
            events=state.events,
        )
