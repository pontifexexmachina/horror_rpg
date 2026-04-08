from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from dead_by_dawn_sim.runner import EncounterResult, EncounterRunner
from dead_by_dawn_sim.state import (
    ActorState,
    ActorStatus,
    EncounterState,
    snapshot_actor,
    synchronize_engagements,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from dead_by_dawn_sim.rules import InterludeTreatmentRule, Ruleset
    from dead_by_dawn_sim.runner_types import ActorMetadata


@dataclass(frozen=True)
class SessionResult:
    plan_id: str
    seed: int
    encounter_results: tuple[EncounterResult, ...]
    final_snapshots: dict[str, dict[str, int | str | dict[str, int]]]
    resources_spent: dict[str, int]
    completed_scenarios: int


class SessionRunner:
    def __init__(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset
        self.encounter_runner = EncounterRunner(ruleset)

    def run_plan(self, plan_id: str, seed: int) -> SessionResult:
        plan = self.ruleset.session_plans[plan_id]
        seed_counter = seed
        protagonist_team = "team_a"
        first_scenario_id = plan.scenario_ids[0]
        state, metadata = self.encounter_runner.build_state_bundle(first_scenario_id, seed_counter)
        carried_team = self._actors_on_team(state.actors, protagonist_team)
        carried_metadata = self._metadata_on_team(metadata, protagonist_team)
        encounter_results: list[EncounterResult] = []
        resources_spent: dict[str, int] = {}

        for index, scenario_id in enumerate(plan.scenario_ids):
            if index == 0:
                scene_state = state
                scene_metadata = metadata
            else:
                seed_counter += 1
                scene_state, scene_metadata = self.encounter_runner.build_state_bundle(
                    scenario_id, seed_counter
                )
                team_actor_ids = {
                    actor_id
                    for actor_id, actor in scene_state.actors.items()
                    if actor.team == protagonist_team
                }
                if team_actor_ids != set(carried_team):
                    raise ValueError(
                        f"Session plan {plan_id} uses incompatible {protagonist_team} composition in {scenario_id}."
                    )
                scene_actors = dict(scene_state.actors)
                for actor_id in team_actor_ids:
                    carried_actor = carried_team[actor_id]
                    fresh_actor = scene_state.actors[actor_id]
                    scene_actors[actor_id] = replace(
                        carried_actor,
                        conditions=(),
                        area_id=fresh_actor.area_id,
                        engaged_with=frozenset(),
                    )
                    scene_metadata[actor_id] = carried_metadata[actor_id]
                scene_state = synchronize_engagements(
                    EncounterState(
                        scenario_id=scene_state.scenario_id,
                        objective=scene_state.objective,
                        areas=scene_state.areas,
                        connections=scene_state.connections,
                        actors=scene_actors,
                        round_number=scene_state.round_number,
                        initiative_order=scene_state.initiative_order,
                        active_actor_id=scene_state.active_actor_id,
                        used_reactions=scene_state.used_reactions,
                        winner=scene_state.winner,
                        events=scene_state.events,
                    )
                )

            result, final_state = self.encounter_runner.run_with_final_state(
                scenario_id=scenario_id,
                seed=seed_counter,
                state=scene_state,
                metadata=scene_metadata,
            )
            encounter_results.append(result)
            carried_team = self._actors_on_team(final_state.actors, protagonist_team)
            carried_metadata = self._metadata_on_team(scene_metadata, protagonist_team)
            carried_team, spent = self._run_interlude(carried_team, plan.interlude.treatments)
            for resource_id, amount in spent.items():
                resources_spent[resource_id] = resources_spent.get(resource_id, 0) + amount

        final_snapshots = {
            actor_id: snapshot_actor(actor) for actor_id, actor in carried_team.items()
        }
        return SessionResult(
            plan_id=plan_id,
            seed=seed,
            encounter_results=tuple(encounter_results),
            final_snapshots=final_snapshots,
            resources_spent=resources_spent,
            completed_scenarios=len(encounter_results),
        )

    def _actors_on_team(
        self,
        actors: Mapping[str, ActorState],
        team: str,
    ) -> dict[str, ActorState]:
        return {actor_id: actor for actor_id, actor in actors.items() if actor.team == team}

    def _metadata_on_team(
        self,
        metadata: Mapping[str, ActorMetadata],
        team: str,
    ) -> dict[str, ActorMetadata]:
        return {actor_id: item for actor_id, item in metadata.items() if item.team == team}

    def _run_interlude(
        self,
        team_a: dict[str, ActorState],
        treatments: list[InterludeTreatmentRule],
    ) -> tuple[dict[str, ActorState], dict[str, int]]:
        actors = {
            actor_id: replace(actor, conditions=(), engaged_with=frozenset())
            for actor_id, actor in team_a.items()
        }
        spent_by_resource: dict[str, int] = {}
        for treatment in treatments:
            actors, spent = self._apply_interlude_treatment(actors, treatment)
            spent_by_resource[treatment.resource] = (
                spent_by_resource.get(treatment.resource, 0) + spent
            )
        return actors, spent_by_resource

    def _apply_interlude_treatment(
        self,
        team_a: dict[str, ActorState],
        treatment: InterludeTreatmentRule,
    ) -> tuple[dict[str, ActorState], int]:
        actors = dict(team_a)
        available = sum(actor.resource_amount(treatment.resource) for actor in actors.values())
        spent = 0
        while available >= treatment.resource_cost:
            target = self._select_treatment_target(actors)
            if target is None:
                break
            healed_hp = min(target.max_hp, target.hp + treatment.heal_amount)
            next_status = target.status
            if treatment.restore_to_normal_on_heal and healed_hp > 0 and target.status in {
                ActorStatus.WOUNDED,
                ActorStatus.CRITICAL,
                ActorStatus.STABLE,
            }:
                next_status = ActorStatus.NORMAL
            next_conditions = () if treatment.clear_conditions else target.conditions
            actors[target.actor_id] = replace(
                target,
                hp=healed_hp,
                status=next_status,
                conditions=next_conditions,
            )
            available -= treatment.resource_cost
            spent += treatment.resource_cost
        remaining = spent
        for actor_id, actor in actors.items():
            deduction = min(actor.resource_amount(treatment.resource), remaining)
            next_resources = dict(actor.resources)
            next_resources[treatment.resource] = actor.resource_amount(treatment.resource) - deduction
            actors[actor_id] = replace(actor, resources=next_resources)
            remaining -= deduction
        return actors, spent

    def _select_treatment_target(
        self,
        actors: dict[str, ActorState],
    ) -> ActorState | None:
        treatable = [
            actor
            for actor in actors.values()
            if actor.status in {ActorStatus.WOUNDED, ActorStatus.CRITICAL, ActorStatus.STABLE}
            or actor.hp < actor.max_hp
        ]
        if not treatable:
            return None
        return min(treatable, key=lambda actor: (actor.hp, actor.stress, actor.actor_id))
