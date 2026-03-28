from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="molt",
        description="Run simple Molt Farm skill-builder operations from the local repository.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    skill_builder_parser = subparsers.add_parser(
        "skill-builder",
        help="Skill-builder operations for running named operations and evaluating skills.",
    )
    skill_builder_subparsers = skill_builder_parser.add_subparsers(
        dest="skill_builder_command",
        required=True,
    )

    _add_run_parser(skill_builder_subparsers)
    _add_eval_skill_parser(skill_builder_subparsers)
    _add_experimental_parser(skill_builder_subparsers)
    return parser


def _add_run_parser(subparsers) -> argparse.ArgumentParser:
    run_parser = subparsers.add_parser("run", help="Execute a named skill-builder operation.")
    run_parser.add_argument("operation", help="Named skill-builder operation.")
    run_parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Override an operation input. Can be repeated.",
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



def _add_experimental_parser(subparsers) -> argparse.ArgumentParser:
    experimental_parser = subparsers.add_parser(
        "experimental",
        help="Optional research tooling that is not part of the core skill loop.",
    )
    experimental_subparsers = experimental_parser.add_subparsers(
        dest="experimental_command",
        required=True,
    )
    _add_analyze_codex_run_parser(experimental_subparsers)
    _add_analyze_codex_corpus_parser(experimental_subparsers)
    _add_probe_codex_trigger_parser(experimental_subparsers)
    _add_find_near_dupe_skills_parser(experimental_subparsers)
    return experimental_parser


def _add_analyze_codex_run_parser(subparsers) -> argparse.ArgumentParser:
    analyze_parser = subparsers.add_parser(
        "analyze-codex-run",
        help="Experimental: analyze one Codex --json run log for observable skill usage.",
    )
    analyze_parser.add_argument(
        "source_path",
        help="Path to one Codex JSONL log file.",
    )
    analyze_parser.add_argument(
        "--output",
        default=None,
        help="Optional output path for the analyzed skill timeline JSON.",
    )
    return analyze_parser


def _add_analyze_codex_corpus_parser(subparsers) -> argparse.ArgumentParser:
    corpus_parser = subparsers.add_parser(
        "analyze-codex-corpus",
        help="Experimental: analyze a manifest of Codex logs and report skill-detection regressions.",
    )
    corpus_parser.add_argument(
        "--manifest",
        required=True,
        help="Path to the Codex corpus manifest JSON file.",
    )
    corpus_parser.add_argument(
        "--output-dir",
        default=None,
        help="Optional output directory for the corpus report and per-case timelines.",
    )
    return corpus_parser


def _add_probe_codex_trigger_parser(subparsers) -> argparse.ArgumentParser:
    probe_parser = subparsers.add_parser(
        "probe-codex-trigger",
        help="Experimental: probe Codex skill-trigger behavior in a clean sandbox.",
    )
    probe_parser.add_argument("skill", help="Primary skill under skills/.")
    probe_parser.add_argument(
        "--with-skill",
        action="append",
        default=[],
        help="Additional local skills to install alongside the primary skill.",
    )
    probe_parser.add_argument(
        "--model",
        default=None,
        help="Optional Codex model override for the probe run.",
    )
    return probe_parser


def _add_find_near_dupe_skills_parser(subparsers) -> argparse.ArgumentParser:
    near_dupe_parser = subparsers.add_parser(
        "find-near-dupe-skills",
        help="Experimental: scan a skills root for potentially confusing near-duplicate skills.",
    )
    near_dupe_parser.add_argument(
        "--skills-root",
        required=True,
        help="Path to the skills root to scan.",
    )
    near_dupe_parser.add_argument(
        "--area",
        action="append",
        default=[],
        help="Optional top-level skill area to include. Can be repeated.",
    )
    near_dupe_parser.add_argument(
        "--output",
        default=None,
        help="Optional output path for the near-dupe report JSON.",
    )
    return near_dupe_parser


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
        if command == "experimental":
            command = f"experimental:{args.experimental_command}"

    if command == "run":
        from .runner import run_workflow

        result = run_workflow(
            project_root=project_root,
            workflow_name=args.operation,
            overrides=parse_overrides(args.input),
        )
        print(
            json.dumps(
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
            )
        )
        return 0 if result.status == "completed" else 1

    if command == "eval-skill":
        from .skill_evaluator import evaluate_skill

        result = evaluate_skill(
            project_root=project_root,
            skill_name=args.skill,
            model=args.model,
            baseline=args.baseline,
            snapshot_current=args.snapshot_current,
        )
        print(json.dumps(result, indent=2))
        return 0


    if command == "experimental:analyze-codex-run":
        from .experimental.codex_timeline import discover_analysis_skill_names, write_codex_skill_timeline

        result = write_codex_skill_timeline(
            Path(args.source_path),
            skill_names=discover_analysis_skill_names(project_root=project_root),
            output_path=Path(args.output) if args.output is not None else None,
        )
        print(json.dumps(result, indent=2))
        return 0

    if command == "experimental:analyze-codex-corpus":
        from .experimental.codex_corpus import analyze_codex_corpus

        result = analyze_codex_corpus(
            project_root=project_root,
            manifest_path=Path(args.manifest),
            output_dir=Path(args.output_dir) if args.output_dir is not None else None,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["passed"] else 1

    if command == "experimental:probe-codex-trigger":
        from .experimental.codex_probe import run_codex_trigger_probe

        result = run_codex_trigger_probe(
            project_root=project_root,
            target_skill=args.skill,
            installed_skills=args.with_skill,
            model=args.model,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["discover_completed"] else 1

    if command == "experimental:find-near-dupe-skills":
        from .experimental.near_dupe_skills import write_skill_near_dupe_report

        try:
            result = write_skill_near_dupe_report(
                project_root=project_root,
                skills_root=Path(args.skills_root),
                areas=args.area,
                output_path=Path(args.output) if args.output is not None else None,
            )
        except (FileNotFoundError, ValueError) as exc:
            parser.error(str(exc))
        print(json.dumps(result, indent=2))
        return 0

    parser.error(f"Unknown command: {command}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
