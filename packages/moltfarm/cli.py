from __future__ import annotations

import argparse
import json
from pathlib import Path

from .skill_evaluator import evaluate_skill
from .runner import run_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="molt",
        description="Run simple Molt Farm workflows from the local repository.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    skill_builder_parser = subparsers.add_parser(
        "skill-builder",
        help="Skill-builder operations for running workflows and evaluating skills.",
    )
    skill_builder_subparsers = skill_builder_parser.add_subparsers(
        dest="skill_builder_command",
        required=True,
    )

    _add_run_parser(skill_builder_subparsers)
    _add_eval_skill_parser(skill_builder_subparsers)

    # Keep the older top-level forms as compatibility aliases.
    _add_run_parser(subparsers)
    _add_eval_skill_parser(subparsers)
    return parser


def _add_run_parser(subparsers) -> argparse.ArgumentParser:
    run_parser = subparsers.add_parser("run", help="Execute a workflow.")
    run_parser.add_argument("workflow", help="Workflow folder name under workflows/.")
    run_parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override a workflow input. Can be repeated.",
    )
    return run_parser


def _add_eval_skill_parser(subparsers) -> argparse.ArgumentParser:
    eval_parser = subparsers.add_parser(
        "eval-skill",
        help="Run a skill eval iteration from skills/<name>/evals/evals.json.",
    )
    eval_parser.add_argument("skill", help="Skill folder name under skills/.")
    eval_parser.add_argument(
        "--baseline",
        choices=["none", "without-skill", "snapshot"],
        default="without-skill",
        help="Baseline to compare against.",
    )
    eval_parser.add_argument(
        "--snapshot-current",
        action="store_true",
        help="Save a snapshot of the current skill into the new iteration directory.",
    )
    eval_parser.add_argument(
        "--model",
        default="gpt-5",
        help="Model to use for eval runs and grading.",
    )
    return eval_parser


def parse_overrides(items: list[str]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"Invalid --input value '{item}'. Expected KEY=VALUE.")
        key, value = item.split("=", 1)
        overrides[key] = value
    return overrides


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    project_root = Path.cwd()

    command = args.command
    if command == "skill-builder":
        command = args.skill_builder_command

    if command == "run":
        result = run_workflow(
            project_root=project_root,
            workflow_name=args.workflow,
            overrides=parse_overrides(args.input),
        )
        print(json.dumps(
            {
                "run_id": result.run_id,
                "workflow": result.workflow,
                "agent": result.agent,
                "status": result.status,
                "run_path": result.run_path,
                "log_path": result.log_path,
                "summary": result.output["summary"],
            },
            indent=2,
        ))
        return 0 if result.status == "completed" else 1

    if command == "eval-skill":
        result = evaluate_skill(
            project_root=project_root,
            skill_name=args.skill,
            model=args.model,
            baseline=args.baseline,
            snapshot_current=args.snapshot_current,
        )
        print(json.dumps(result, indent=2))
        return 0

    parser.error(f"Unknown command: {command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
