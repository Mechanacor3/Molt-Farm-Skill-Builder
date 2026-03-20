from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runner import run_workflow


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="molt",
        description="Run simple Molt Farm workflows from the local repository.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Execute a workflow.")
    run_parser.add_argument("workflow", help="Workflow folder name under workflows/.")
    run_parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override a workflow input. Can be repeated.",
    )
    return parser


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

    if args.command == "run":
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
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
