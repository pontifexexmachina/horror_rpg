from __future__ import annotations

from dataclasses import dataclass, replace

from dead_by_dawn_sim.rules import Ruleset
from dead_by_dawn_sim.runner import EncounterResult, EncounterRunner
from dead_by_dawn_sim.state import ActorState, ActorStatus, EncounterState, synchronize_engagements


@dataclass(frozen=True)
class SessionResult:
    plan_id: str
    seed: int
    encounter_results: tuple[EncounterResult, ...]
    final_snapshots: dict[str, dict[str, int | str | dict[str, int]]]
    medkits_spent: int
    completed_scenarios: int


class SessionRunner:
    def __init__(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset
        self.encounter_runner = EncounterRunner(ruleset)

    def run_plan(self, plan_id: str, seed: int) -> SessionResult:
        plan = self.ruleset.session_plans[plan_id]
        seed_counter = seed
        first_scenario_id = plan.scenario_ids[0]
        state, metadata = self.encounter_runner.build_state_bundle(first_scenario_id, seed_counter)
        carried_team_a = {
            actor_id: actor
            for actor_id, actor in state.actors.items()
            if actor_id.startswith("team_a_")
        }
        carried_metadata = {
            actor_id: item for actor_id, item in metadata.items() if actor_id.startswith("team_a_")
        }
        encounter_results: list[EncounterResult] = []
        medkits_spent = 0

        for index, scenario_id in enumerate(plan.scenario_ids):
            if index == 0:
                scene_state = state
                scene_metadata = metadata
            else:
                seed_counter += 1
                scene_state, scene_metadata = self.encounter_runner.build_state_bundle(
                    scenario_id, seed_counter
                )
                team_a_ids = [
                    actor_id for actor_id in scene_state.actors if actor_id.startswith("team_a_")
                ]
                if set(team_a_ids) != set(carried_team_a):
                    raise ValueError(
                        f"Session plan {plan_id} uses incompatible team_a composition in {scenario_id}."
                    )
                scene_actors = dict(scene_state.actors)
                for actor_id in team_a_ids:
                    carried_actor = carried_team_a[actor_id]
                    fresh_actor = scene_state.actors[actor_id]
                    scene_actors[actor_id] = replace(
                        carried_actor,
                        conditions=tuple(),
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
            carried_team_a = {
                actor_id: actor
                for actor_id, actor in final_state.actors.items()
                if actor_id.startswith("team_a_")
            }
            carried_metadata = {
                actor_id: item
                for actor_id, item in scene_metadata.items()
                if actor_id.startswith("team_a_")
            }
            carried_team_a, spent = self._field_treat_team(carried_team_a)
            medkits_spent += spent

        final_snapshots = {
            actor_id: self._snapshot(actor) for actor_id, actor in carried_team_a.items()
        }
        return SessionResult(
            plan_id=plan_id,
            seed=seed,
            encounter_results=tuple(encounter_results),
            final_snapshots=final_snapshots,
            medkits_spent=medkits_spent,
            completed_scenarios=len(encounter_results),
        )

    def _field_treat_team(self, team_a: dict[str, ActorState]) -> tuple[dict[str, ActorState], int]:
        actors = {
            actor_id: replace(actor, conditions=tuple(), engaged_with=frozenset())
            for actor_id, actor in team_a.items()
        }
        pool = sum(actor.medkits for actor in actors.values())
        spent = 0
        while pool > 0:
            treatable = [
                actor
                for actor in actors.values()
                if actor.status in {ActorStatus.WOUNDED, ActorStatus.CRITICAL}
                or actor.hp < actor.max_hp
            ]
            if not treatable:
                break
            target = min(treatable, key=lambda actor: (actor.hp, actor.stress, actor.actor_id))
            healed_hp = min(target.max_hp, target.hp + 2)
            next_status = target.status
            if healed_hp > 0 and target.status in {ActorStatus.WOUNDED, ActorStatus.CRITICAL}:
                next_status = ActorStatus.NORMAL
            actors[target.actor_id] = replace(target, hp=healed_hp, status=next_status)
            pool -= 1
            spent += 1
        remaining = spent
        updated: dict[str, ActorState] = {}
        for actor_id, actor in actors.items():
            deduction = min(actor.medkits, remaining)
            updated[actor_id] = replace(actor, medkits=actor.medkits - deduction)
            remaining -= deduction
        return updated, spent

    def _snapshot(self, actor: ActorState) -> dict[str, int | str | dict[str, int]]:
        return {
            "hp": actor.hp,
            "status": actor.status.value,
            "stress": actor.stress,
            "shrouds": actor.shrouds,
            "area_id": actor.area_id,
            "ammo": dict(actor.ammo),
            "bandages": actor.bandages,
            "medkits": actor.medkits,
        }
