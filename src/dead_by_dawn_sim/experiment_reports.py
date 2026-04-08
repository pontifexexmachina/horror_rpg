from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from statistics import mean
from typing import TYPE_CHECKING

from dead_by_dawn_sim.runner_types import ActorMetadata, ContributionStats, EncounterResult

if TYPE_CHECKING:
    from dead_by_dawn_sim.session import SessionResult

Snapshot = Mapping[str, object]


@dataclass(frozen=True)
class BenchmarkReport:
    suite_id: str
    rules_version: str
    seed_policy: str
    runs: int
    metrics: dict[str, object]
    scenario_breakdown: dict[str, dict[str, object]]


@dataclass(frozen=True)
class SessionBenchmarkReport:
    plan_id: str
    rules_version: str
    seed_policy: str
    runs: int
    metrics: dict[str, object]


def _clamp_rate(value: float) -> float:
    return max(0.0, min(1.0, value))


def _percentile(values: list[int], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percentile)
    return float(ordered[index])


def _snapshot_status(snapshot: Snapshot) -> str:
    value = snapshot["status"]
    return value if isinstance(value, str) else str(value)


def _snapshot_int(snapshot: Snapshot, key: str) -> int:
    value = snapshot[key]
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return int(value)
    raise TypeError(f"Snapshot field {key} is not numeric: {value!r}")


def _snapshot_resources(snapshot: Snapshot) -> dict[str, int]:
    value = snapshot.get("resources")
    if isinstance(value, Mapping):
        return {str(key): int(amount) for key, amount in value.items()}
    return {}


def _status_rates_from_snapshots(snapshots: Sequence[Snapshot]) -> dict[str, float]:
    total = len(snapshots)
    if total == 0:
        return {"normal": 0.0, "wounded": 0.0, "critical": 0.0, "dead": 0.0, "broken": 0.0}
    return {
        "normal": sum(1 for snapshot in snapshots if _snapshot_status(snapshot) == "normal") / total,
        "wounded": sum(1 for snapshot in snapshots if _snapshot_status(snapshot) == "wounded") / total,
        "critical": sum(1 for snapshot in snapshots if _snapshot_status(snapshot) == "critical") / total,
        "dead": sum(1 for snapshot in snapshots if _snapshot_status(snapshot) == "dead") / total,
        "broken": sum(1 for snapshot in snapshots if _snapshot_status(snapshot) == "broken") / total,
    }


def _team_status_rates(results: list[EncounterResult]) -> dict[str, dict[str, float]]:
    snapshots_by_team: dict[str, list[Snapshot]] = {}
    for result in results:
        for actor_id, snapshot in result.actor_snapshots.items():
            team = result.actor_metadata[actor_id].team
            snapshots_by_team.setdefault(team, []).append(snapshot)
    return {
        team: _status_rates_from_snapshots(team_snapshots)
        for team, team_snapshots in sorted(snapshots_by_team.items())
    }


def _action_frequencies(results: list[EncounterResult]) -> dict[str, float]:
    counts: dict[str, int] = {}
    total_actions = 0
    for result in results:
        for action_id, count in result.action_counts.items():
            counts[action_id] = counts.get(action_id, 0) + count
            total_actions += count
    if total_actions == 0:
        return {}
    return {action_id: count / total_actions for action_id, count in sorted(counts.items())}


def _merge_stats(left: ContributionStats | None, right: ContributionStats) -> ContributionStats:
    if left is None:
        return right
    return ContributionStats(
        actions_taken=left.actions_taken + right.actions_taken,
        pushes_used=left.pushes_used + right.pushes_used,
        damage_dealt=left.damage_dealt + right.damage_dealt,
        healing_done=left.healing_done + right.healing_done,
        stress_inflicted=left.stress_inflicted + right.stress_inflicted,
        control_applied=left.control_applied + right.control_applied,
        enemy_wounded=left.enemy_wounded + right.enemy_wounded,
        enemy_critical=left.enemy_critical + right.enemy_critical,
        enemy_dead=left.enemy_dead + right.enemy_dead,
        enemy_broken=left.enemy_broken + right.enemy_broken,
    )


def _contribution_payload(stats: ContributionStats, encounters: int) -> dict[str, float | int]:
    divisor = max(1, encounters)
    return {
        "total_actions_taken": stats.actions_taken,
        "total_pushes_used": stats.pushes_used,
        "total_damage_dealt": stats.damage_dealt,
        "total_healing_done": stats.healing_done,
        "total_stress_inflicted": stats.stress_inflicted,
        "total_control_applied": stats.control_applied,
        "total_enemy_wounded": stats.enemy_wounded,
        "total_enemy_critical": stats.enemy_critical,
        "total_enemy_dead": stats.enemy_dead,
        "total_enemy_broken": stats.enemy_broken,
        "avg_actions_taken": stats.actions_taken / divisor,
        "avg_pushes_used": stats.pushes_used / divisor,
        "avg_damage_dealt": stats.damage_dealt / divisor,
        "avg_healing_done": stats.healing_done / divisor,
        "avg_stress_inflicted": stats.stress_inflicted / divisor,
        "avg_control_applied": stats.control_applied / divisor,
        "avg_enemy_wounded": stats.enemy_wounded / divisor,
        "avg_enemy_critical": stats.enemy_critical / divisor,
        "avg_enemy_dead": stats.enemy_dead / divisor,
        "avg_enemy_broken": stats.enemy_broken / divisor,
    }


def _summarize_actor_contributions(results: list[EncounterResult]) -> dict[str, dict[str, object]]:
    totals: dict[str, ContributionStats] = {}
    metadata: dict[str, ActorMetadata] = {}
    appearances: dict[str, int] = {}
    for result in results:
        for actor_id, contribution in result.actor_contributions.items():
            totals[actor_id] = _merge_stats(totals.get(actor_id), contribution)
            metadata[actor_id] = result.actor_metadata[actor_id]
            appearances[actor_id] = appearances.get(actor_id, 0) + 1
    return {
        actor_id: {
            "team": metadata[actor_id].team,
            "name": metadata[actor_id].name,
            "template_id": metadata[actor_id].template_id,
            "policy_id": metadata[actor_id].policy_id,
            "encounters": appearances[actor_id],
            **_contribution_payload(totals[actor_id], appearances[actor_id]),
        }
        for actor_id in sorted(totals)
    }


def _summarize_archetype_contributions(results: list[EncounterResult]) -> dict[str, dict[str, object]]:
    totals: dict[str, ContributionStats] = {}
    appearances: dict[str, int] = {}
    for result in results:
        for actor_id, contribution in result.actor_contributions.items():
            meta = result.actor_metadata[actor_id]
            archetype_id = f"{meta.team}:{meta.template_id}:{meta.policy_id}"
            totals[archetype_id] = _merge_stats(totals.get(archetype_id), contribution)
            appearances[archetype_id] = appearances.get(archetype_id, 0) + 1
    summary: dict[str, dict[str, object]] = {}
    for archetype_id in sorted(totals):
        team, template_id, policy_id = archetype_id.split(":", maxsplit=2)
        summary[archetype_id] = {
            "team": team,
            "template_id": template_id,
            "policy_id": policy_id,
            "encounters": appearances[archetype_id],
            **_contribution_payload(totals[archetype_id], appearances[archetype_id]),
        }
    return summary


def summarize_benchmark_suite_results(results: list[EncounterResult]) -> dict[str, object]:
    total_actors = [snapshot for result in results for snapshot in result.actor_snapshots.values()]
    rounds = [result.rounds for result in results]
    stress_values = [_snapshot_int(snapshot, "stress") for snapshot in total_actors]
    shroud_values = [_snapshot_int(snapshot, "shrouds") for snapshot in total_actors]
    draws = sum(1 for result in results if result.winner == "draw")
    team_a_wins = sum(1 for result in results if result.winner == "team_a")
    team_a_win_rate = team_a_wins / len(results)
    draw_rate = draws / len(results)
    team_b_win_rate = _clamp_rate(1 - team_a_win_rate - draw_rate)
    return {
        "win_rate_team_a": _clamp_rate(team_a_win_rate),
        "draw_rate": _clamp_rate(draw_rate),
        "win_rate_team_b": team_b_win_rate,
        "avg_rounds": mean(rounds),
        "p50_rounds": _percentile(rounds, 0.5),
        "p90_rounds": _percentile(rounds, 0.9),
        "avg_stress": mean(stress_values),
        "max_stress": float(max(stress_values)),
        "avg_shrouds": mean(shroud_values),
        "status_rates": _status_rates_from_snapshots(total_actors),
        "team_status_rates": _team_status_rates(results),
        "avg_pushes_per_encounter": mean([result.push_count for result in results]),
        "action_frequencies": _action_frequencies(results),
        "archetype_contributions": _summarize_archetype_contributions(results),
    }


def summarize_scenario_results(results: list[EncounterResult]) -> dict[str, object]:
    rounds = [result.rounds for result in results]
    wins = sum(1 for result in results if result.winner == "team_a")
    draws = sum(1 for result in results if result.winner == "draw")
    team_a_win_rate = wins / len(results)
    draw_rate = draws / len(results)
    team_b_win_rate = _clamp_rate(1 - team_a_win_rate - draw_rate)
    stress_values = [
        _snapshot_int(snapshot, "stress")
        for result in results
        for snapshot in result.actor_snapshots.values()
    ]
    shroud_values = [
        _snapshot_int(snapshot, "shrouds")
        for result in results
        for snapshot in result.actor_snapshots.values()
    ]
    all_snapshots = [snapshot for result in results for snapshot in result.actor_snapshots.values()]
    return {
        "avg_rounds": mean(rounds),
        "p50_rounds": _percentile(rounds, 0.5),
        "p90_rounds": _percentile(rounds, 0.9),
        "team_a_win_rate": _clamp_rate(team_a_win_rate),
        "draw_rate": _clamp_rate(draw_rate),
        "team_b_win_rate": team_b_win_rate,
        "avg_stress": mean(stress_values),
        "max_stress": float(max(stress_values)),
        "avg_shrouds": mean(shroud_values),
        "status_rates": _status_rates_from_snapshots(all_snapshots),
        "team_status_rates": _team_status_rates(results),
        "avg_pushes_per_encounter": mean([result.push_count for result in results]),
        "action_frequencies": _action_frequencies(results),
        "actor_contributions": _summarize_actor_contributions(results),
        "archetype_contributions": _summarize_archetype_contributions(results),
    }


def summarize_session_results(results: list[SessionResult]) -> dict[str, object]:
    final_snapshots = [snapshot for result in results for snapshot in result.final_snapshots.values()]
    encounter_counts = [result.completed_scenarios for result in results]
    resource_ids = sorted(
        {
            resource_id
            for result in results
            for snapshot in result.final_snapshots.values()
            for resource_id in _snapshot_resources(snapshot)
        }
        | {
            resource_id
            for result in results
            for resource_id in result.resources_spent
        }
    )
    avg_resources_spent = {
        resource_id: mean([result.resources_spent.get(resource_id, 0) for result in results])
        for resource_id in resource_ids
    }
    avg_remaining_resources = {
        resource_id: mean([
            _snapshot_resources(snapshot).get(resource_id, 0) for snapshot in final_snapshots
        ])
        for resource_id in resource_ids
    }
    return {
        "avg_completed_scenarios": mean(encounter_counts),
        "avg_resources_spent": avg_resources_spent,
        "avg_remaining_resources": avg_remaining_resources,
        "final_team_status_rates": _status_rates_from_snapshots(final_snapshots),
        "avg_final_stress": mean([_snapshot_int(snapshot, "stress") for snapshot in final_snapshots]),
        "avg_final_hp": mean([_snapshot_int(snapshot, "hp") for snapshot in final_snapshots]),
    }
