from __future__ import annotations

from statistics import mean

from dead_by_dawn_sim.rules import Ruleset
from dead_by_dawn_sim.runner import (
    ActorMetadata,
    ContributionStats,
    EncounterResult,
    EncounterRunner,
)


class BenchmarkReport:
    def __init__(
        self,
        *,
        suite_id: str,
        rules_version: str,
        seed_policy: str,
        runs: int,
        metrics: dict[str, object],
        scenario_breakdown: dict[str, dict[str, object]],
    ) -> None:
        self.suite_id = suite_id
        self.rules_version = rules_version
        self.seed_policy = seed_policy
        self.runs = runs
        self.metrics = metrics
        self.scenario_breakdown = scenario_breakdown


class ExperimentRunner:
    def __init__(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset
        self.runner = EncounterRunner(ruleset)

    def run_benchmark_suite(self, suite_id: str, runs: int, seed: int = 0) -> BenchmarkReport:
        suite = self.ruleset.benchmark_suites[suite_id]
        all_results: list[EncounterResult] = []
        scenario_breakdown: dict[str, dict[str, object]] = {}
        seed_counter = seed
        for scenario_id in suite.scenario_ids:
            scenario_results: list[EncounterResult] = []
            for _ in range(runs):
                result = self.runner.run(scenario_id, seed_counter)
                seed_counter += 1
                all_results.append(result)
                scenario_results.append(result)
            scenario_breakdown[scenario_id] = self._summarize_scenario(scenario_results)
        return BenchmarkReport(
            suite_id=suite_id,
            rules_version=self.ruleset.version,
            seed_policy=f"start={seed}",
            runs=runs,
            metrics=self._summarize_results(all_results),
            scenario_breakdown=scenario_breakdown,
        )

    def _clamp_rate(self, value: float) -> float:
        return max(0.0, min(1.0, value))

    def _percentile(self, values: list[int], percentile: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        index = round((len(ordered) - 1) * percentile)
        return float(ordered[index])

    def _status_rates_from_snapshots(
        self,
        snapshots: list[dict[str, int | str]],
    ) -> dict[str, float]:
        total = len(snapshots)
        if total == 0:
            return {
                "normal": 0.0,
                "wounded": 0.0,
                "critical": 0.0,
                "dead": 0.0,
                "broken": 0.0,
            }
        return {
            "normal": sum(1 for snapshot in snapshots if snapshot["status"] == "normal") / total,
            "wounded": sum(1 for snapshot in snapshots if snapshot["status"] == "wounded") / total,
            "critical": sum(1 for snapshot in snapshots if snapshot["status"] == "critical")
            / total,
            "dead": sum(1 for snapshot in snapshots if snapshot["status"] == "dead") / total,
            "broken": sum(1 for snapshot in snapshots if snapshot["status"] == "broken") / total,
        }

    def _team_status_rates(
        self,
        results: list[EncounterResult],
    ) -> dict[str, dict[str, float]]:
        team_a_snapshots = [
            snapshot
            for result in results
            for actor_id, snapshot in result.actor_snapshots.items()
            if actor_id.startswith("team_a_")
        ]
        team_b_snapshots = [
            snapshot
            for result in results
            for actor_id, snapshot in result.actor_snapshots.items()
            if actor_id.startswith("team_b_")
        ]
        return {
            "team_a": self._status_rates_from_snapshots(team_a_snapshots),
            "team_b": self._status_rates_from_snapshots(team_b_snapshots),
        }

    def _action_frequencies(self, results: list[EncounterResult]) -> dict[str, float]:
        counts: dict[str, int] = {}
        total_actions = 0
        for result in results:
            for action_id, count in result.action_counts.items():
                counts[action_id] = counts.get(action_id, 0) + count
                total_actions += count
        if total_actions == 0:
            return {}
        return {action_id: count / total_actions for action_id, count in sorted(counts.items())}

    def _summarize_actor_contributions(
        self, results: list[EncounterResult]
    ) -> dict[str, dict[str, object]]:
        totals: dict[str, ContributionStats] = {}
        metadata: dict[str, ActorMetadata] = {}
        appearances: dict[str, int] = {}
        for result in results:
            for actor_id, contribution in result.actor_contributions.items():
                totals[actor_id] = self._merge_stats(totals.get(actor_id), contribution)
                metadata[actor_id] = result.actor_metadata[actor_id]
                appearances[actor_id] = appearances.get(actor_id, 0) + 1
        return {
            actor_id: {
                "team": metadata[actor_id].team,
                "name": metadata[actor_id].name,
                "template_id": metadata[actor_id].template_id,
                "persona_id": metadata[actor_id].persona_id,
                "encounters": appearances[actor_id],
                **self._contribution_payload(totals[actor_id], appearances[actor_id]),
            }
            for actor_id in sorted(totals)
        }

    def _summarize_archetype_contributions(
        self, results: list[EncounterResult]
    ) -> dict[str, dict[str, object]]:
        totals: dict[str, ContributionStats] = {}
        appearances: dict[str, int] = {}
        for result in results:
            for actor_id, contribution in result.actor_contributions.items():
                meta = result.actor_metadata[actor_id]
                archetype_id = f"{meta.team}:{meta.template_id}:{meta.persona_id}"
                totals[archetype_id] = self._merge_stats(totals.get(archetype_id), contribution)
                appearances[archetype_id] = appearances.get(archetype_id, 0) + 1
        summary: dict[str, dict[str, object]] = {}
        for archetype_id in sorted(totals):
            team, template_id, persona_id = archetype_id.split(":", maxsplit=2)
            summary[archetype_id] = {
                "team": team,
                "template_id": template_id,
                "persona_id": persona_id,
                "encounters": appearances[archetype_id],
                **self._contribution_payload(totals[archetype_id], appearances[archetype_id]),
            }
        return summary

    def _merge_stats(
        self, left: ContributionStats | None, right: ContributionStats
    ) -> ContributionStats:
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

    def _contribution_payload(
        self, stats: ContributionStats, encounters: int
    ) -> dict[str, float | int]:
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

    def _summarize_scenario(self, results: list[EncounterResult]) -> dict[str, object]:
        rounds = [result.rounds for result in results]
        wins = sum(1 for result in results if result.winner == "team_a")
        draws = sum(1 for result in results if result.winner == "draw")
        team_a_win_rate = wins / len(results)
        draw_rate = draws / len(results)
        team_b_win_rate = self._clamp_rate(1 - team_a_win_rate - draw_rate)
        stress_values = [
            int(snapshot["stress"])
            for result in results
            for snapshot in result.actor_snapshots.values()
        ]
        shroud_values = [
            int(snapshot["shrouds"])
            for result in results
            for snapshot in result.actor_snapshots.values()
        ]
        all_snapshots = [
            snapshot for result in results for snapshot in result.actor_snapshots.values()
        ]
        return {
            "avg_rounds": mean(rounds),
            "p50_rounds": self._percentile(rounds, 0.5),
            "p90_rounds": self._percentile(rounds, 0.9),
            "team_a_win_rate": self._clamp_rate(team_a_win_rate),
            "draw_rate": self._clamp_rate(draw_rate),
            "team_b_win_rate": team_b_win_rate,
            "avg_stress": mean(stress_values),
            "max_stress": float(max(stress_values)),
            "avg_shrouds": mean(shroud_values),
            "status_rates": self._status_rates_from_snapshots(all_snapshots),
            "team_status_rates": self._team_status_rates(results),
            "avg_pushes_per_encounter": mean([result.push_count for result in results]),
            "action_frequencies": self._action_frequencies(results),
            "actor_contributions": self._summarize_actor_contributions(results),
            "archetype_contributions": self._summarize_archetype_contributions(results),
        }

    def _summarize_results(self, results: list[EncounterResult]) -> dict[str, object]:
        total_actors = [
            snapshot for result in results for snapshot in result.actor_snapshots.values()
        ]
        rounds = [result.rounds for result in results]
        stress_values = [int(snapshot["stress"]) for snapshot in total_actors]
        shroud_values = [int(snapshot["shrouds"]) for snapshot in total_actors]
        draws = sum(1 for result in results if result.winner == "draw")
        team_a_wins = sum(1 for result in results if result.winner == "team_a")
        team_a_win_rate = team_a_wins / len(results)
        draw_rate = draws / len(results)
        team_b_win_rate = self._clamp_rate(1 - team_a_win_rate - draw_rate)
        return {
            "win_rate_team_a": self._clamp_rate(team_a_win_rate),
            "draw_rate": self._clamp_rate(draw_rate),
            "win_rate_team_b": team_b_win_rate,
            "avg_rounds": mean(rounds),
            "p50_rounds": self._percentile(rounds, 0.5),
            "p90_rounds": self._percentile(rounds, 0.9),
            "avg_stress": mean(stress_values),
            "max_stress": float(max(stress_values)),
            "avg_shrouds": mean(shroud_values),
            "status_rates": self._status_rates_from_snapshots(total_actors),
            "team_status_rates": self._team_status_rates(results),
            "avg_pushes_per_encounter": mean([result.push_count for result in results]),
            "action_frequencies": self._action_frequencies(results),
            "archetype_contributions": self._summarize_archetype_contributions(results),
        }
