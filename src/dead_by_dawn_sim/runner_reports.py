from __future__ import annotations

from dead_by_dawn_sim.runner_types import ActorMetadata, ContributionStats, EncounterResult
from dead_by_dawn_sim.state import ActorStatus, EncounterState, snapshot_actor


def status_rank(status: ActorStatus | str | object) -> int:
    value = getattr(status, "value", status)
    if not isinstance(value, str):
        value = str(value)
    return {
        "normal": 0,
        "wounded": 1,
        "critical": 2,
        "stable": 3,
        "dead": 4,
        "broken": 4,
    }.get(value, 0)


def accumulate_contribution(
    current: ContributionStats,
    *,
    choice_push: bool,
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
        before_rank = status_rank(before_actor.status)
        after_rank = status_rank(after_actor.status)
        if after_rank > before_rank:
            enemy_wounded += int(before_rank < status_rank("wounded") <= after_rank)
            enemy_critical += int(before_rank < status_rank("critical") <= after_rank)
            enemy_dead += int(before_rank < status_rank("dead") <= after_rank)
            enemy_broken += int(before_rank < status_rank("broken") <= after_rank)
    return ContributionStats(
        actions_taken=current.actions_taken + 1,
        pushes_used=current.pushes_used + int(choice_push),
        damage_dealt=current.damage_dealt + damage_dealt,
        healing_done=current.healing_done + healing_done,
        stress_inflicted=current.stress_inflicted + stress_inflicted,
        control_applied=current.control_applied + control_applied,
        enemy_wounded=current.enemy_wounded + enemy_wounded,
        enemy_critical=current.enemy_critical + enemy_critical,
        enemy_dead=current.enemy_dead + enemy_dead,
        enemy_broken=current.enemy_broken + enemy_broken,
    )


def finish_encounter(
    state: EncounterState,
    *,
    scenario_id: str,
    seed: int,
    winner: str,
    rounds: int,
    metadata: dict[str, ActorMetadata],
    contributions: dict[str, ContributionStats],
    action_counts: dict[str, int],
    push_count: int,
) -> EncounterResult:
    snapshots = {actor_id: snapshot_actor(actor) for actor_id, actor in state.actors.items()}
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
