from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from ..storage import write_json, write_text
from .codex_timeline import discover_analysis_skill_names, write_codex_skill_timeline


def analyze_codex_corpus(
    project_root: Path,
    *,
    manifest_path: Path,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    resolved_project_root = project_root.resolve()
    resolved_manifest = manifest_path.resolve()
    manifest_cases = _load_corpus_manifest(resolved_manifest)
    resolved_output_dir = (
        output_dir.resolve()
        if output_dir is not None
        else resolved_project_root
        / "tmp"
        / "codex-skill-corpus"
        / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    )
    skill_names = discover_analysis_skill_names(project_root=resolved_project_root)

    results: list[dict[str, Any]] = []
    missing_case_ids: list[str] = []
    failed_case_ids: list[str] = []

    for case in manifest_cases:
        case_id = str(case["id"])
        raw_case_path = str(case["path"])
        resolved_case_path = _resolve_manifest_case_path(
            project_root=resolved_project_root,
            raw_path=raw_case_path,
        )
        case_result: dict[str, Any] = {
            "id": case_id,
            "description": str(case.get("description") or ""),
            "source_path": str(resolved_case_path),
            "expected_observed_invocation_order": case.get("expected_observed_invocation_order"),
            "expected_first_seen_skill_order": case.get("expected_first_seen_skill_order"),
            "min_invocation_event_count": case.get("min_invocation_event_count"),
            "max_invocation_event_count": case.get("max_invocation_event_count"),
            "errors": [],
        }

        if not resolved_case_path.is_file():
            case_result["errors"].append(f"Log file not found: {resolved_case_path}")
            missing_case_ids.append(case_id)
        else:
            try:
                timeline = write_codex_skill_timeline(
                    resolved_case_path,
                    skill_names=skill_names,
                    output_path=resolved_output_dir / "cases" / f"{case_id}.skill-trace.json",
                )
            except Exception as exc:  # pragma: no cover - defensive reporting path
                case_result["errors"].append(f"Analysis failed: {exc}")
            else:
                actual_order = list(timeline.get("observed_invocation_order", []))
                actual_first_seen = list(timeline.get("first_seen_skill_order", []))
                actual_invocation_count = len(actual_order)
                case_result.update(
                    {
                        "timeline_path": timeline["output_path"],
                        "actual_observed_invocation_order": actual_order,
                        "actual_first_seen_skill_order": actual_first_seen,
                        "actual_invocation_event_count": actual_invocation_count,
                    }
                )
                _validate_case_expectations(case_result)

        case_result["passed"] = not case_result["errors"]
        if not case_result["passed"]:
            failed_case_ids.append(case_id)
        results.append(case_result)

    report = {
        "manifest_path": str(resolved_manifest),
        "output_dir": str(resolved_output_dir),
        "generated_at": datetime.now().isoformat(),
        "passed": not failed_case_ids,
        "case_count": len(results),
        "passed_case_count": sum(1 for result in results if result["passed"]),
        "failed_case_count": len(failed_case_ids),
        "missing_case_ids": missing_case_ids,
        "failed_case_ids": failed_case_ids,
        "results": results,
    }
    report_path = write_json(resolved_output_dir / "report.json", report)
    report_markdown_path = write_text(
        resolved_output_dir / "report.md",
        _render_markdown_report(report),
    )
    return {
        **report,
        "report_path": str(report_path),
        "report_markdown_path": str(report_markdown_path),
    }


def _load_corpus_manifest(manifest_path: Path) -> list[dict[str, Any]]:
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        cases = payload
    elif isinstance(payload, dict):
        cases = payload.get("cases")
    else:
        cases = None
    if not isinstance(cases, list):
        raise ValueError(f"Invalid Codex corpus manifest: {manifest_path}")

    normalized_cases: list[dict[str, Any]] = []
    for case in cases:
        if not isinstance(case, dict):
            raise ValueError(f"Invalid Codex corpus case in {manifest_path}: {case!r}")
        if "id" not in case or "path" not in case:
            raise ValueError(f"Codex corpus case is missing required fields in {manifest_path}: {case!r}")
        normalized_cases.append(case)
    return normalized_cases


def _resolve_manifest_case_path(*, project_root: Path, raw_path: str) -> Path:
    expanded = Path(os.path.expanduser(os.path.expandvars(raw_path)))
    if expanded.is_absolute():
        return expanded.resolve()
    return (project_root / expanded).resolve()


def _validate_case_expectations(case_result: dict[str, Any]) -> None:
    actual_order = list(case_result.get("actual_observed_invocation_order") or [])
    actual_first_seen = list(case_result.get("actual_first_seen_skill_order") or [])
    actual_count = int(case_result.get("actual_invocation_event_count") or 0)

    expected_order = case_result.get("expected_observed_invocation_order")
    if expected_order is not None and list(expected_order) != actual_order:
        case_result["errors"].append(
            "Observed invocation order mismatch: "
            f"expected {list(expected_order)!r}, got {actual_order!r}"
        )

    expected_first_seen = case_result.get("expected_first_seen_skill_order")
    if expected_first_seen is not None and list(expected_first_seen) != actual_first_seen:
        case_result["errors"].append(
            "First-seen skill order mismatch: "
            f"expected {list(expected_first_seen)!r}, got {actual_first_seen!r}"
        )

    minimum = case_result.get("min_invocation_event_count")
    if minimum is not None and actual_count < int(minimum):
        case_result["errors"].append(
            f"Invocation event count {actual_count} is below minimum {int(minimum)}"
        )

    maximum = case_result.get("max_invocation_event_count")
    if maximum is not None and actual_count > int(maximum):
        case_result["errors"].append(
            f"Invocation event count {actual_count} exceeds maximum {int(maximum)}"
        )


def _render_markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# Codex Skill Corpus Report",
        "",
        f"- Passed: {report['passed']}",
        f"- Cases: {report['case_count']}",
        f"- Passed cases: {report['passed_case_count']}",
        f"- Failed cases: {report['failed_case_count']}",
        "",
        "## Cases",
    ]
    for result in report["results"]:
        lines.append("")
        lines.append(f"### {result['id']}")
        if result.get("description"):
            lines.append(result["description"])
        lines.append(f"- Passed: {result['passed']}")
        lines.append(f"- Source: {result['source_path']}")
        if "timeline_path" in result:
            lines.append(f"- Timeline: {result['timeline_path']}")
            lines.append(
                "- Observed order: "
                f"{result.get('actual_observed_invocation_order', [])!r}"
            )
            lines.append(
                "- First-seen order: "
                f"{result.get('actual_first_seen_skill_order', [])!r}"
            )
        if result["errors"]:
            lines.append("- Errors:")
            for error in result["errors"]:
                lines.append(f"  - {error}")
    lines.append("")
    return "\n".join(lines)
