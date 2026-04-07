from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from dead_by_dawn_sim.experiments import ExperimentRunner
from dead_by_dawn_sim.rules import count_ruleset_entities, load_ruleset
from dead_by_dawn_sim.runner import EncounterRunner
from dead_by_dawn_sim.session import SessionRunner


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ddb-sim")
    parser.add_argument("--data-dir", default="data")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--scenario", required=True)
    run_parser.add_argument("--seed", type=int, required=True)
    run_parser.add_argument("--output")
    benchmark_parser = subparsers.add_parser("benchmark")
    benchmark_parser.add_argument("--suite", required=True)
    benchmark_parser.add_argument("--runs", type=int, required=True)
    benchmark_parser.add_argument("--seed", type=int, default=0)
    benchmark_parser.add_argument("--output")
    session_parser = subparsers.add_parser("session")
    session_parser.add_argument("--plan", required=True)
    session_parser.add_argument("--seed", type=int, required=True)
    session_parser.add_argument("--output")
    session_benchmark_parser = subparsers.add_parser("session-benchmark")
    session_benchmark_parser.add_argument("--plan", required=True)
    session_benchmark_parser.add_argument("--runs", type=int, required=True)
    session_benchmark_parser.add_argument("--seed", type=int, default=0)
    session_benchmark_parser.add_argument("--output")
    return parser


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return {key: _to_jsonable(item) for key, item in vars(value).items()}
    if isinstance(value, dict):
        return {key: _to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_to_jsonable(item) for item in value]
    return value


def _write_output(payload: dict[str, Any], output_path: str | None) -> None:
    rendered = json.dumps(_to_jsonable(payload), indent=2, sort_keys=True)
    if output_path is None:
        print(rendered)
        return
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    ruleset = load_ruleset(args.data_dir)
    if args.command == "validate":
        print(
            json.dumps(
                {"rules_version": ruleset.version, "counts": count_ruleset_entities(ruleset)},
                indent=2,
                sort_keys=True,
            )
        )
        return 0
    if args.command == "run":
        result = EncounterRunner(ruleset).run(args.scenario, args.seed)
        _write_output(
            {
                "rules_version": ruleset.version,
                "scenario_id": result.scenario_id,
                "seed": result.seed,
                "winner": result.winner,
                "rounds": result.rounds,
                "actor_metadata": result.actor_metadata,
                "actor_snapshots": result.actor_snapshots,
                "actor_contributions": result.actor_contributions,
                "events": list(result.events),
            },
            args.output,
        )
        return 0
    if args.command == "benchmark":
        report = ExperimentRunner(ruleset).run_benchmark_suite(
            args.suite, args.runs, seed=args.seed
        )
        _write_output(
            {
                "rules_version": report.rules_version,
                "suite_id": report.suite_id,
                "seed_policy": report.seed_policy,
                "runs": report.runs,
                "metrics": report.metrics,
                "scenario_breakdown": report.scenario_breakdown,
            },
            args.output,
        )
        return 0
    if args.command == "session":
        result = SessionRunner(ruleset).run_plan(args.plan, args.seed)
        _write_output(
            {
                "rules_version": ruleset.version,
                "plan_id": result.plan_id,
                "seed": result.seed,
                "completed_scenarios": result.completed_scenarios,
                "medkits_spent": result.medkits_spent,
                "final_snapshots": result.final_snapshots,
                "encounter_results": list(result.encounter_results),
            },
            args.output,
        )
        return 0
    if args.command == "session-benchmark":
        report = ExperimentRunner(ruleset).run_session_plan(args.plan, args.runs, seed=args.seed)
        _write_output(
            {
                "rules_version": report.rules_version,
                "plan_id": report.plan_id,
                "seed_policy": report.seed_policy,
                "runs": report.runs,
                "metrics": report.metrics,
            },
            args.output,
        )
        return 0
    raise ValueError(f"Unsupported command {args.command}")
