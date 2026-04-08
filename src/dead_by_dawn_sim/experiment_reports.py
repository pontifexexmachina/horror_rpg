from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from statistics import mean
from typing import TYPE_CHECKING

from dead_by_dawn_sim.runner_types import ContributionStats, EncounterResult

if TYPE_CHECKING:
    from dead_by_dawn_sim.runner_types import ActorMetadata
    from dead_by_dawn_sim.session import SessionResult

Snapshot = Mapping[str, object]
_STATUS_KEYS = ("normal", "wounded", "critical", "dead", "broken")
_CONTRIBUTION_FIELDS = (
    "actions_taken",
    "pushes_used",
    "damage_dealt",
    "healing_done",
    "stress_inflicted",
    "control_applied",
    "enemy_wounded",
    "enemy_critical",
    "enemy_dead",
    "enemy_broken",
)


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
        return dict.fromkeys(_STATUS_KEYS, 0.0)
    return {
        status: sum(1 for snapshot in snapshots if _snapshot_status(snapshot) == status) / total
        for status in _STATUS_KEYS
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
        **{field: getattr(left, field) + getattr(right, field) for field in _CONTRIBUTION_FIELDS}
    )


def _contribution_payload(stats: ContributionStats, encounters: int) -> dict[str, float | int]:
    divisor = max(1, encounters)
    totals = {f"total_{field}": getattr(stats, field) for field in _CONTRIBUTION_FIELDS}
    averages = {f"avg_{field}": getattr(stats, field) / divisor for field in _CONTRIBUTION_FIELDS}
    return {**totals, **averages}


def _summarize_contributions(
    results: list[EncounterResult],
    *,
    group_key: Callable[[str, ActorMetadata], str],
    summary_key: Callable[[str, ActorMetadata], dict[str, object]],
) -> dict[str, dict[str, object]]:
    totals: dict[str, ContributionStats] = {}
    appearances: dict[str, int] = {}
    details: dict[str, dict[str, object]] = {}
    for result in results:
        for actor_id, contribution in result.actor_contributions.items():
            meta = result.actor_metadata[actor_id]
            key = group_key(actor_id, meta)
            totals[key] = _merge_stats(totals.get(key), contribution)
            appearances[key] = appearances.get(key, 0) + 1
            details[key] = summary_key(actor_id, meta)
    return {
        key: {
            **details[key],
            "encounters": appearances[key],
            **_contribution_payload(totals[key], appearances[key]),
        }
        for key in sorted(totals)
    }


def _summarize_actor_contributions(results: list[EncounterResult]) -> dict[str, dict[str, object]]:
    return _summarize_contributions(
        results,
        group_key=lambda actor_id, _meta: actor_id,
        summary_key=lambda _actor_id, meta: {
            "team": meta.team,
            "name": meta.name,
            "template_id": meta.template_id,
            "policy_id": meta.policy_id,
        },
    )


def _summarize_archetype_contributions(results: list[EncounterResult]) -> dict[str, dict[str, object]]:
    return _summarize_contributions(
        results,
        group_key=lambda _actor_id, meta: f"{meta.team}:{meta.template_id}:{meta.policy_id}",
        summary_key=lambda _actor_id, meta: {
            "team": meta.team,
            "template_id": meta.template_id,
            "policy_id": meta.policy_id,
        },
    )


def _encounter_summary(
    results: list[EncounterResult],
    *,
    team_a_key: str,
    team_b_key: str,
    include_actor_contributions: bool,
) -> dict[str, object]:
    all_snapshots = [snapshot for result in results for snapshot in result.actor_snapshots.values()]
    rounds = [result.rounds for result in results]
    stress_values = [_snapshot_int(snapshot, "stress") for snapshot in all_snapshots]
    shroud_values = [_snapshot_int(snapshot, "shrouds") for snapshot in all_snapshots]
    draws = sum(1 for result in results if result.winner == "draw")
    team_a_win_rate = sum(1 for result in results if result.winner == "team_a") / len(results)
    draw_rate = draws / len(results)
    summary: dict[str, object] = {
        team_a_key: _clamp_rate(team_a_win_rate),
        "draw_rate": _clamp_rate(draw_rate),
        team_b_key: _clamp_rate(1 - team_a_win_rate - draw_rate),
        "avg_rounds": mean(rounds),
        "p50_rounds": _percentile(rounds, 0.5),
        "p90_rounds": _percentile(rounds, 0.9),
        "avg_stress": mean(stress_values),
        "max_stress": float(max(stress_values)),
        "avg_shrouds": mean(shroud_values),
        "status_rates": _status_rates_from_snapshots(all_snapshots),
        "team_status_rates": _team_status_rates(results),
        "avg_pushes_per_encounter": mean([result.push_count for result in results]),
        "action_frequencies": _action_frequencies(results),
        "archetype_contributions": _summarize_archetype_contributions(results),
    }
    if include_actor_contributions:
        summary["actor_contributions"] = _summarize_actor_contributions(results)
    return summary


def summarize_benchmark_suite_results(results: list[EncounterResult]) -> dict[str, object]:
    return _encounter_summary(
        results,
        team_a_key="win_rate_team_a",
        team_b_key="win_rate_team_b",
        include_actor_contributions=False,
    )


def summarize_scenario_results(results: list[EncounterResult]) -> dict[str, object]:
    return _encounter_summary(
        results,
        team_a_key="team_a_win_rate",
        team_b_key="team_b_win_rate",
        include_actor_contributions=True,
    )


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
        | {resource_id for result in results for resource_id in result.resources_spent}
    )
    avg_resources_spent = {
        resource_id: mean([result.resources_spent.get(resource_id, 0) for result in results])
        for resource_id in resource_ids
    }
    avg_remaining_resources = {
        resource_id: mean(
            [_snapshot_resources(snapshot).get(resource_id, 0) for snapshot in final_snapshots]
        )
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
