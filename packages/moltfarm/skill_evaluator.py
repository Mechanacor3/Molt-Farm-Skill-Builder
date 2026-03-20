from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .models import AgentDefinition, Skill, SkillEvalCase
from .runner import execute_task
from .skill_evals import (
    load_skill_eval_suite,
    next_iteration_dir,
    resolve_eval_case_files,
    snapshot_skill,
)
from .skill_loader import discover_skills, load_skill
from .storage import write_json, write_text


class AssertionGrade(BaseModel):
    text: str
    passed: bool
    evidence: str


class GradingSummary(BaseModel):
    passed: int
    failed: int
    total: int
    pass_rate: float


class GradingPayload(BaseModel):
    assertion_results: list[AssertionGrade]
    summary: GradingSummary


def evaluate_skill(
    project_root: Path,
    *,
    skill_name: str,
    model: str = "gpt-5",
    baseline: str = "without-skill",
    snapshot_current: bool = False,
) -> dict[str, Any]:
    skills_by_name = discover_skills(project_root / "skills")
    skill = skills_by_name.get(skill_name)
    if skill is None:
        raise ValueError(f"Unknown skill '{skill_name}'.")

    suite = load_skill_eval_suite(skill)
    if suite is None:
        raise ValueError(f"Skill '{skill_name}' has no eval suite at evals/evals.json.")
    if not suite.cases:
        raise ValueError(f"Skill '{skill_name}' has no eval cases.")

    iteration_dir = next_iteration_dir(skill)
    if snapshot_current:
        snapshot_dir = snapshot_skill(skill, iteration_dir)
    else:
        snapshot_dir = None

    configurations = [("with_skill", skill)]
    if baseline == "without-skill":
        configurations.append(("without_skill", None))
    elif baseline == "snapshot":
        snapshot_skill_file = _find_latest_snapshot_skill(skill, exclude_dir=iteration_dir)
        if snapshot_skill_file is None:
            raise ValueError(
                f"No prior snapshot available for skill '{skill_name}'. Run with --snapshot-current first."
            )
        configurations.append(("old_skill", load_skill(snapshot_skill_file)))
    else:
        raise ValueError(f"Unsupported baseline '{baseline}'.")

    case_summaries: list[dict[str, Any]] = []
    feedback_template: dict[str, str] = {}
    for case in suite.cases:
        case_result = _evaluate_case(
            project_root=project_root,
            case=case,
            skill=skill,
            configurations=configurations,
            model=model,
            iteration_dir=iteration_dir,
        )
        case_summaries.append(case_result)
        feedback_template[f"eval-{case.case_id}"] = ""

    feedback_path = write_json(iteration_dir / "feedback.json", feedback_template)
    benchmark = _build_benchmark(case_summaries)
    benchmark["skill_name"] = skill.name
    benchmark["iteration_dir"] = str(iteration_dir.relative_to(project_root))
    benchmark["baseline"] = baseline
    benchmark["snapshot_current"] = snapshot_current
    if snapshot_dir is not None:
        benchmark["snapshot_dir"] = str(snapshot_dir.relative_to(project_root))
    benchmark["feedback_path"] = str(feedback_path.relative_to(project_root))
    benchmark_path = write_json(iteration_dir / "benchmark.json", benchmark)
    return {
        "skill_name": skill.name,
        "iteration_dir": str(iteration_dir.relative_to(project_root)),
        "benchmark_path": str(benchmark_path.relative_to(project_root)),
        "feedback_path": str(feedback_path.relative_to(project_root)),
        "baseline": baseline,
        "snapshot_dir": (
            str(snapshot_dir.relative_to(project_root)) if snapshot_dir is not None else None
        ),
        "cases": case_summaries,
        "benchmark": benchmark,
    }


def _evaluate_case(
    *,
    project_root: Path,
    case: SkillEvalCase,
    skill: Skill,
    configurations: list[tuple[str, Skill | None]],
    model: str,
    iteration_dir: Path,
) -> dict[str, Any]:
    case_dir = iteration_dir / f"eval-{case.case_id}"
    resolved_files = resolve_eval_case_files(skill, case)
    relative_files = [
        str(path.relative_to(project_root))
        for path in resolved_files
    ]

    config_results: dict[str, Any] = {}
    for label, configured_skill in configurations:
        config_dir = case_dir / label
        outputs_dir = config_dir / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        task_input = {
            "task": case.prompt,
            "output_dir": str(outputs_dir.relative_to(project_root)),
        }
        for index, relative_path in enumerate(relative_files, start=1):
            task_input[f"input_file_{index}"] = relative_path

        agent = AgentDefinition(
            name=f"{skill.name}-eval-worker",
            description=f"Eval worker for skill {skill.name}.",
            model=model,
            context_policy="least_context",
            runtime="openai_agents",
        )
        attached_skills = [configured_skill] if configured_skill is not None else []
        status, output = execute_task(
            project_root=project_root,
            agent=agent,
            skills=attached_skills,
            task_input=task_input,
        )

        write_json(
            config_dir / "result.json",
            {
                "status": status,
                "task_input": task_input,
                "output": output,
            },
        )
        write_text(outputs_dir / "summary.txt", output["summary"])
        write_json(config_dir / "timing.json", _build_timing_payload(output))
        write_json(config_dir / "trace.json", output.get("trace", {}))

        grading = _grade_eval_output(
            project_root=project_root,
            model=model,
            case=case,
            output=output,
            attached_skill=configured_skill,
        )
        write_json(config_dir / "grading.json", grading)
        config_results[label] = {
            "status": status,
            "result_path": str((config_dir / "result.json").relative_to(project_root)),
            "timing_path": str((config_dir / "timing.json").relative_to(project_root)),
            "trace_path": str((config_dir / "trace.json").relative_to(project_root)),
            "grading_path": str((config_dir / "grading.json").relative_to(project_root)),
            "summary_path": str((outputs_dir / "summary.txt").relative_to(project_root)),
            "pass_rate": grading["summary"]["pass_rate"],
            "metrics": output.get("metrics", {}),
        }

    return {
        "case_id": case.case_id,
        "prompt": case.prompt,
        "expected_output": case.expected_output,
        "files": relative_files,
        "configurations": config_results,
    }


def _build_timing_payload(output: dict[str, Any]) -> dict[str, Any]:
    metrics = output.get("metrics", {}) or {}
    usage = metrics.get("usage", {}) or {}
    return {
        "duration_ms": metrics.get("duration_ms", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "requests": usage.get("requests", 0),
    }


def _grade_eval_output(
    *,
    project_root: Path,
    model: str,
    case: SkillEvalCase,
    output: dict[str, Any],
    attached_skill: Skill | None,
) -> dict[str, Any]:
    if not case.assertions:
        return {
            "assertion_results": [],
            "summary": {"passed": 0, "failed": 0, "total": 0, "pass_rate": 0.0},
            "mode": "no_assertions",
        }

    sdk = _load_sdk(project_root)
    prompt = _build_grading_prompt(
        case=case,
        output=output,
        attached_skill=attached_skill,
    )
    grader = sdk.Agent(
        name="skill-eval-grader",
        model=model,
        instructions=(
            "Grade eval assertions against the provided output. "
            "Each assertion_result must include text, passed, and evidence. "
            "Require concrete evidence for PASS. "
            "If an assertion cannot be verified from the output, mark it false."
        ),
        output_type=GradingPayload,
    )
    result = sdk.Runner.run_sync(grader, prompt)
    payload = _coerce_grading_payload(result.final_output)
    payload["mode"] = "llm_grader"
    return payload


def _build_grading_prompt(
    *,
    case: SkillEvalCase,
    output: dict[str, Any],
    attached_skill: Skill | None,
) -> str:
    skill_label = attached_skill.name if attached_skill is not None else "no-skill baseline"
    lines = [
        f"Configuration: {skill_label}",
        f"Prompt: {case.prompt}",
        f"Expected output: {case.expected_output}",
        "Assertions:",
    ]
    for assertion in case.assertions:
        lines.append(f"- {assertion}")
    lines.extend(
        [
            "",
            "Actual output summary:",
            output["summary"],
            "",
            "Return JSON only.",
        ]
    )
    return "\n".join(lines)


def _parse_grading_json(raw_text: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("Grader did not return JSON.")
        payload = json.loads(raw_text[start : end + 1])

    assertion_results = payload.get("assertion_results") or []
    summary = payload.get("summary") or {}
    if not isinstance(assertion_results, list) or not isinstance(summary, dict):
        raise ValueError("Invalid grading payload shape.")
    return {
        "assertion_results": assertion_results,
        "summary": {
            "passed": int(summary.get("passed", 0) or 0),
            "failed": int(summary.get("failed", 0) or 0),
            "total": int(summary.get("total", 0) or 0),
            "pass_rate": float(summary.get("pass_rate", 0.0) or 0.0),
        },
    }


def _coerce_grading_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, GradingPayload):
        return value.model_dump()
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        if isinstance(dumped, dict):
            return _parse_grading_json(json.dumps(dumped))
    return _parse_grading_json(str(value))


def _build_benchmark(case_summaries: list[dict[str, Any]]) -> dict[str, Any]:
    labels = sorted(
        {
            label
            for case in case_summaries
            for label in case["configurations"]
        }
    )
    run_summary: dict[str, Any] = {}
    for label in labels:
        pass_rates = [
            case["configurations"][label]["pass_rate"]
            for case in case_summaries
            if label in case["configurations"]
        ]
        durations = [
            int(case["configurations"][label]["metrics"].get("duration_ms", 0) or 0)
            for case in case_summaries
            if label in case["configurations"]
        ]
        tokens = [
            int(
                (
                    case["configurations"][label]["metrics"].get("usage", {}) or {}
                ).get("total_tokens", 0)
                or 0
            )
            for case in case_summaries
            if label in case["configurations"]
        ]
        run_summary[label] = {
            "pass_rate": _stats(pass_rates),
            "duration_ms": _stats(durations),
            "tokens": _stats(tokens),
        }

    if "with_skill" in run_summary:
        baseline_label = "old_skill" if "old_skill" in run_summary else "without_skill"
        if baseline_label in run_summary:
            run_summary["delta"] = {
                "pass_rate": run_summary["with_skill"]["pass_rate"]["mean"]
                - run_summary[baseline_label]["pass_rate"]["mean"],
                "duration_ms": run_summary["with_skill"]["duration_ms"]["mean"]
                - run_summary[baseline_label]["duration_ms"]["mean"],
                "tokens": run_summary["with_skill"]["tokens"]["mean"]
                - run_summary[baseline_label]["tokens"]["mean"],
                "baseline": baseline_label,
            }
    return {"run_summary": run_summary}


def _stats(values: list[int | float]) -> dict[str, float]:
    if not values:
        return {"mean": 0.0, "stddev": 0.0}
    if len(values) == 1:
        return {"mean": float(values[0]), "stddev": 0.0}
    return {
        "mean": float(statistics.mean(values)),
        "stddev": float(statistics.pstdev(values)),
    }


def _load_sdk(project_root: Path):
    from . import runner

    load_dotenv = runner._load_dotenv(project_root)
    if load_dotenv is not None:
        load_dotenv(project_root / ".env", override=False)
    sdk = runner._import_openai_agents_sdk(project_root)
    sdk.set_tracing_disabled(True)
    return sdk


def _find_latest_snapshot_skill(skill: Skill, *, exclude_dir: Path) -> Path | None:
    workspace_root = skill.path / "evals" / "workspace"
    if not workspace_root.exists():
        return None
    candidates = sorted(
        (
            child for child in workspace_root.iterdir()
            if child.is_dir() and child != exclude_dir and child.name.startswith("iteration-")
        ),
        key=lambda path: int(path.name.split("-")[1]),
        reverse=True,
    )
    for iteration_dir in candidates:
        snapshot_skill_file = iteration_dir / "skill-snapshot" / skill.name / "SKILL.md"
        if snapshot_skill_file.is_file():
            return snapshot_skill_file
    return None
