from __future__ import annotations

from dataclasses import replace as dc_replace

from _pytest.capture import CaptureFixture
from _pytest.monkeypatch import MonkeyPatch

from dead_by_dawn_sim.actions import ActionChoice
from dead_by_dawn_sim.cli import main
from dead_by_dawn_sim.experiments import ExperimentRunner
from dead_by_dawn_sim.personas import POLICY_REGISTRY
from dead_by_dawn_sim.rules import Ruleset, load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner
from dead_by_dawn_sim.session import SessionRunner
from dead_by_dawn_sim.state import EncounterState, synchronize_engagements, update_actor


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
    assert medic["policy_id"] == "tactician"
    assert "avg_healing_done" in medic


def test_session_runner_carries_resources_forward() -> None:
    ruleset = load_ruleset()
    result = SessionRunner(ruleset).run_plan("core_night", seed=3)
    assert result.completed_scenarios == 3
    assert result.medkits_spent >= 0
    assert "team_a_medic_2" in result.final_snapshots
    medic_snapshot = result.final_snapshots["team_a_medic_2"]
    assert "medkits" in medic_snapshot
    assert "ammo" in medic_snapshot


def test_session_benchmark_report_contains_resource_metrics() -> None:
    report = ExperimentRunner(load_ruleset()).run_session_plan("core_night", runs=2, seed=9)
    assert "avg_medkits_spent" in report.metrics
    assert "avg_remaining_sidearm_ammo" in report.metrics
    assert "final_team_status_rates" in report.metrics


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
    assert main(["session", "--plan", "core_night", "--seed", "5"]) == 0
    session_output = capsys.readouterr().out
    assert '"plan_id": "core_night"' in session_output
    assert '"final_snapshots"' in session_output
    assert main(["session-benchmark", "--plan", "core_night", "--runs", "1", "--seed", "5"]) == 0
    session_benchmark_output = capsys.readouterr().out
    assert '"avg_medkits_spent"' in session_benchmark_output


def test_runner_respects_action_costs_for_shriek() -> None:
    ruleset = load_ruleset()
    terror = ruleset.actors["terror"]
    assert ruleset.actions["shriek"].action_cost == 2
    assert terror.actions == ["shriek"]
    report = ExperimentRunner(ruleset).run_benchmark_suite("combat_canonical", runs=1, seed=0)
    scenario = report.scenario_breakdown["four_pc_vs_control_mix"]
    action_frequencies = scenario["action_frequencies"]
    assert isinstance(action_frequencies, dict)
    assert "shriek" in action_frequencies


class _AttackSpamPersona:
    def choose_action(
        self,
        legal_actions: list[ActionChoice],
        _state: EncounterState,
        _ruleset: Ruleset,
    ) -> ActionChoice:
        for action_id in ("attack", "unarmed_attack", "fall_back"):
            for choice in legal_actions:
                if choice.action_id == action_id:
                    return choice
        return legal_actions[0]


def test_runner_accepts_custom_policy_resolver() -> None:
    ruleset = load_ruleset()

    class _AlwaysFirstPolicy:
        def choose_action(
            self,
            legal_actions: list[ActionChoice],
            state: EncounterState,
            ruleset: Ruleset,
        ) -> ActionChoice:
            del state, ruleset
            return legal_actions[0]

    def resolve_policy(actor_id: str, metadata: object) -> _AlwaysFirstPolicy:
        del actor_id, metadata
        return _AlwaysFirstPolicy()

    runner = EncounterRunner(ruleset, policy_resolver=resolve_policy)
    result = runner.run("single_pc_vs_slasher", seed=7)
    assert result.rounds >= 1
    assert result.winner in {"team_a", "team_b", "draw"}


def test_runner_allows_only_one_attack_per_turn(monkeypatch: MonkeyPatch) -> None:
    ruleset = load_ruleset()
    limited_ruleset = dc_replace(
        ruleset,
        core=ruleset.core.model_copy(update={"max_rounds": 1}),
    )
    runner = EncounterRunner(limited_ruleset)
    state, metadata = runner.build_state_bundle("single_pc_vs_slasher", seed=4)
    actor_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_a"))
    target_id = next(actor_id for actor_id in state.actors if actor_id.startswith("team_b"))
    engaged_state = synchronize_engagements(
        update_actor(
            state, dc_replace(state.actor(actor_id), area_id=state.actor(target_id).area_id)
        )
    )
    custom_metadata = {
        key: (dc_replace(value, policy_id="attack_spam") if key == actor_id else value)
        for key, value in metadata.items()
    }
    monkeypatch.setitem(POLICY_REGISTRY, "attack_spam", _AttackSpamPersona())
    result = runner.run_from_state(
        scenario_id="single_pc_vs_slasher",
        seed=4,
        state=engaged_state,
        metadata=custom_metadata,
    )
    assert (
        result.action_counts.get("attack", 0) + result.action_counts.get("unarmed_attack", 0) == 1
    )


def test_validate_loads_updated_shriek_cost() -> None:
    ruleset = load_ruleset()
    assert ruleset.actions["shriek"].action_cost == 2
