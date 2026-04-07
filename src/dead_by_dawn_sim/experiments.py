from __future__ import annotations

from dead_by_dawn_sim.experiment_reports import (
    BenchmarkReport,
    SessionBenchmarkReport,
    summarize_benchmark_suite_results,
    summarize_scenario_results,
    summarize_session_results,
)
from dead_by_dawn_sim.rules import Ruleset
from dead_by_dawn_sim.runner import EncounterRunner
from dead_by_dawn_sim.session import SessionRunner


class ExperimentRunner:
    def __init__(self, ruleset: Ruleset) -> None:
        self.ruleset = ruleset
        self.runner = EncounterRunner(ruleset)
        self.session_runner = SessionRunner(ruleset)

    def run_benchmark_suite(self, suite_id: str, runs: int, seed: int = 0) -> BenchmarkReport:
        suite = self.ruleset.benchmark_suites[suite_id]
        all_results = []
        scenario_breakdown: dict[str, dict[str, object]] = {}
        seed_counter = seed
        for scenario_id in suite.scenario_ids:
            scenario_results = []
            for _ in range(runs):
                result = self.runner.run(scenario_id, seed_counter)
                seed_counter += 1
                all_results.append(result)
                scenario_results.append(result)
            scenario_breakdown[scenario_id] = summarize_scenario_results(scenario_results)
        return BenchmarkReport(
            suite_id=suite_id,
            rules_version=self.ruleset.version,
            seed_policy=f"start={seed}",
            runs=runs,
            metrics=summarize_benchmark_suite_results(all_results),
            scenario_breakdown=scenario_breakdown,
        )

    def run_session_plan(self, plan_id: str, runs: int, seed: int = 0) -> SessionBenchmarkReport:
        results = [self.session_runner.run_plan(plan_id, seed + offset) for offset in range(runs)]
        return SessionBenchmarkReport(
            plan_id=plan_id,
            rules_version=self.ruleset.version,
            seed_policy=f"start={seed}",
            runs=runs,
            metrics=summarize_session_results(results),
        )
