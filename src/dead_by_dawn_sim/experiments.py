from __future__ import annotations

from dataclasses import dataclass
from statistics import mean

from dead_by_dawn_sim.rules import Ruleset
from dead_by_dawn_sim.runner import EncounterResult, EncounterRunner


@dataclass(frozen=True)
class BenchmarkReport:
    suite_id: str
    rules_version: str
    seed_policy: str
    runs: int
    metrics: dict[str, float]
    scenario_breakdown: dict[str, dict[str, float | str]]


class ExperimentRunner:
    def __init__(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset
        self.runner = EncounterRunner(ruleset)

    def run_benchmark_suite(self, suite_id: str, runs: int, seed: int = 0) -> BenchmarkReport:
        suite = self.ruleset.benchmark_suites[suite_id]
        all_results: list[EncounterResult] = []
        scenario_breakdown: dict[str, dict[str, float | str]] = {}
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

    def _summarize_scenario(self, results: list[EncounterResult]) -> dict[str, float | str]:
        rounds = [result.rounds for result in results]
        wins = sum(1 for result in results if result.winner == "team_a")
        stress_values = [
            snapshot["stress"]
            for result in results
            for snapshot in result.actor_snapshots.values()
            if isinstance(snapshot["stress"], int)
        ]
        return {
            "avg_rounds": mean(rounds),
            "team_a_win_rate": wins / len(results),
            "avg_stress": mean(stress_values),
        }

    def _summarize_results(self, results: list[EncounterResult]) -> dict[str, float]:
        total_actors = [
            snapshot for result in results for snapshot in result.actor_snapshots.values()
        ]
        wounded = sum(1 for snapshot in total_actors if snapshot["status"] == "wounded")
        critical = sum(1 for snapshot in total_actors if snapshot["status"] == "critical")
        dead = sum(1 for snapshot in total_actors if snapshot["status"] == "dead")
        return {
            "win_rate_team_a": sum(1 for result in results if result.winner == "team_a")
            / len(results),
            "avg_rounds": mean([result.rounds for result in results]),
            "wounded_rate": wounded / len(total_actors),
            "critical_rate": critical / len(total_actors),
            "death_rate": dead / len(total_actors),
            "avg_stress": mean(
                [
                    snapshot["stress"]
                    for snapshot in total_actors
                    if isinstance(snapshot["stress"], int)
                ]
            ),
        }
