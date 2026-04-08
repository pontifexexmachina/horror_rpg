from __future__ import annotations

from random import Random
from typing import TYPE_CHECKING

from dead_by_dawn_sim.runner_types import ActorMetadata
from dead_by_dawn_sim.state import (
    ActorState,
    EncounterState,
    append_event,
    build_actor_state,
    synchronize_engagements,
)

if TYPE_CHECKING:
    from dead_by_dawn_sim.rules import Ruleset, ScenarioSideEntry


def build_state_bundle(
    ruleset: Ruleset, scenario_id: str, seed: int
) -> tuple[EncounterState, dict[str, ActorMetadata]]:
    scenario = ruleset.scenarios[scenario_id]
    rng = Random(seed)
    actors: dict[str, ActorState] = {}
    metadata: dict[str, ActorMetadata] = {}

    def add_side(team_label: str, entries: list[ScenarioSideEntry]) -> None:
        counter = 1
        for entry in entries:
            template = ruleset.actors[entry.template_id]
            policy_id = entry.policy_id or template.default_policy
            for _ in range(entry.count):
                actor_id = f"{team_label}_{template.id}_{counter}"
                name = f"{template.name} {counter}"
                actors[actor_id] = build_actor_state(
                    actor_id=actor_id,
                    team=team_label,
                    template=template,
                    ruleset=ruleset,
                    name=name,
                    start_area=entry.start_area or scenario.areas[0].id,
                )
                metadata[actor_id] = ActorMetadata(
                    actor_id=actor_id,
                    team=team_label,
                    name=name,
                    template_id=template.id,
                    policy_id=policy_id,
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
        scenario_id=scenario_id,
        objective=scenario.objective,
        areas={area.id: area for area in scenario.areas},
        connections=tuple(scenario.connections),
        actors=actors,
        round_number=1,
        initiative_order=initiative,
        active_actor_id=None,
        used_reactions=frozenset(),
    )
    state = synchronize_engagements(state)
    state = append_event(
        state,
        "Scenario "
        f"{scenario_id} initialized with policies "
        f"{ {actor_id: item.policy_id for actor_id, item in metadata.items()} }.",
    )
    return state, metadata
