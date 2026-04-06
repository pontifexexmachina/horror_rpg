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
    assert left.actor_metadata == right.actor_metadata
    assert left.actor_snapshots == right.actor_snapshots
    assert left.actor_contributions == right.actor_contributions
    assert left.action_counts == right.action_counts
    assert left.push_count == right.push_count


def test_benchmark_report_contains_required_metrics() -> None:
    report = ExperimentRunner(load_ruleset()).run_benchmark_suite("core", runs=2, seed=11)
    assert "avg_rounds" in report.metrics
    assert "win_rate_team_a" in report.metrics
    assert "status_rates" in report.metrics
    assert "team_status_rates" in report.metrics
    assert "action_frequencies" in report.metrics
    assert "archetype_contributions" in report.metrics
    assert "four_pc_vs_slasher" in report.scenario_breakdown
    scenario = report.scenario_breakdown["four_pc_vs_slasher"]
    assert "p90_rounds" in scenario
    assert "avg_pushes_per_encounter" in scenario
    assert "team_status_rates" in scenario
    assert "actor_contributions" in scenario
    assert "archetype_contributions" in scenario
    team_b_win_rate = scenario["team_b_win_rate"]
    assert isinstance(team_b_win_rate, float)
    assert 0.0 <= team_b_win_rate <= 1.0


def test_scenario_contributions_expose_party_roles() -> None:
    report = ExperimentRunner(load_ruleset()).run_benchmark_suite("core", runs=1, seed=17)
    scenario = report.scenario_breakdown["four_pc_vs_slasher"]
    actor_contributions = scenario["actor_contributions"]
    assert isinstance(actor_contributions, dict)
    assert "team_a_medic_2" in actor_contributions
    medic = actor_contributions["team_a_medic_2"]
    assert medic["template_id"] == "medic"
    assert medic["persona_id"] == "tactician"
    assert "avg_healing_done" in medic


def test_cli_validate_and_run_commands(capsys: CaptureFixture[str]) -> None:
    assert main(["validate"]) == 0
    validate_output = capsys.readouterr().out
    assert '"rules_version": "0.1.0"' in validate_output
    assert main(["run", "--scenario", "single_pc_vs_slasher", "--seed", "5"]) == 0
    run_output = capsys.readouterr().out
    assert '"scenario_id": "single_pc_vs_slasher"' in run_output
    assert '"actor_contributions"' in run_output
    assert main(["benchmark", "--suite", "core", "--runs", "1", "--seed", "5"]) == 0
    benchmark_output = capsys.readouterr().out
    assert '"action_frequencies"' in benchmark_output
    assert '"team_status_rates"' in benchmark_output
    assert '"archetype_contributions"' in benchmark_output
