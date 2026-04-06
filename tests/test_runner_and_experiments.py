from __future__ import annotations

from _pytest.capture import CaptureFixture

from dead_by_dawn_sim.cli import main
from dead_by_dawn_sim.experiments import ExperimentRunner
from dead_by_dawn_sim.rules import load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner


def test_runner_is_seed_reproducible() -> None:
    ruleset = load_ruleset()
    runner = EncounterRunner(ruleset)
    left = runner.run("single_pc_vs_slasher", seed=7)
    right = runner.run("single_pc_vs_slasher", seed=7)
    assert left.winner == right.winner
    assert left.rounds == right.rounds
    assert left.actor_snapshots == right.actor_snapshots


def test_benchmark_report_contains_required_metrics() -> None:
    report = ExperimentRunner(load_ruleset()).run_benchmark_suite("core", runs=2, seed=11)
    assert "avg_rounds" in report.metrics
    assert "win_rate_team_a" in report.metrics
    assert "single_pc_vs_slasher" in report.scenario_breakdown


def test_cli_validate_and_run_commands(capsys: CaptureFixture[str]) -> None:
    assert main(["validate"]) == 0
    validate_output = capsys.readouterr().out
    assert '"rules_version": "0.1.0"' in validate_output
    assert main(["run", "--scenario", "single_pc_vs_slasher", "--seed", "5"]) == 0
    run_output = capsys.readouterr().out
    assert '"scenario_id": "single_pc_vs_slasher"' in run_output
