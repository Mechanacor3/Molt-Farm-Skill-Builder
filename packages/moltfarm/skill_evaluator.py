from __future__ import annotations

import json
import statistics
from difflib import SequenceMatcher
from collections import defaultdict
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .models import AgentDefinition, EvalCheck, Skill, SkillEvalCase
from .runner import execute_task
from .skill_evals import (
    load_skill_eval_suite,
    next_iteration_dir,
    resolve_eval_case_files,
    snapshot_skill,
)
from .skill_loader import discover_skills, load_skill
from .storage import write_json, write_text

TASK_UPLIFT_CATEGORIES = ("goal", "evidence")
SECONDARY_COMPARISON_CATEGORIES = ("format", "trigger")


class AssertionGrade(BaseModel):
    text: str
    passed: bool
    evidence: str
    category: str = "goal"
    weight: float = 1.0


class GradingSummary(BaseModel):
    passed: int
    failed: int
    total: int
    pass_rate: float
    weighted_pass_rate: float = 0.0


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
    if baseline == "none":
        pass
    elif baseline == "without-skill":
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
    relative_files = [str(path.relative_to(project_root)) for path in resolved_files]

    config_results: dict[str, Any] = {}
    baseline_label: str | None = None
    for label, configured_skill in configurations:
        if label != "with_skill":
            baseline_label = label
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
        timing = _build_timing_payload(output)
        write_json(config_dir / "timing.json", timing)
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
            "weighted_pass_rate": grading["summary"]["weighted_pass_rate"],
            "category_scores": grading["category_scores"],
            "metrics": output.get("metrics", {}),
            "timing": timing,
        }

    comparison: dict[str, Any] | None = None
    comparison_path: str | None = None
    if baseline_label is not None and "with_skill" in config_results and baseline_label in config_results:
        comparison = _build_case_comparison(
            with_skill=config_results["with_skill"],
            baseline=config_results[baseline_label],
            baseline_label=baseline_label,
        )
        comparison_path = str(
            write_json(case_dir / "comparison.json", comparison).relative_to(project_root)
        )

    return {
        "case_id": case.case_id,
        "prompt": case.prompt,
        "expected_output": case.expected_output,
        "files": relative_files,
        "configurations": config_results,
        "comparison": comparison,
        "comparison_path": comparison_path,
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
    llm_payload = _empty_grading_payload(mode="no_checks")
    if case.checks:
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
                "Grade eval checks against the provided output. "
                "Copy each check text exactly into assertion_results.text, in the same order as provided. "
                "Each assertion_result must include text, passed, and evidence. "
                "Require concrete evidence for PASS. "
                "If a check cannot be verified from the output, mark it false. "
                "Do not invent missing evidence."
            ),
            output_type=GradingPayload,
        )
        result = sdk.Runner.run_sync(grader, prompt)
        llm_payload = _align_grading_payload(
            checks=case.checks,
            payload=_coerce_grading_payload(result.final_output),
            mode="llm_grader",
        )

    trace_payload = _grade_trace_requirements(case=case, output=output, attached_skill=attached_skill)
    return _merge_grading_payloads(llm_payload, trace_payload)


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
        "Checks:",
    ]
    for check in case.checks:
        lines.append(f"- [{check.category} | weight={check.weight:g}] {check.text}")
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


def _grade_trace_requirements(
    *,
    case: SkillEvalCase,
    output: dict[str, Any],
    attached_skill: Skill | None,
) -> dict[str, Any]:
    if not case.required_skill_activations or attached_skill is None:
        return _empty_grading_payload(mode="trace_requirements")

    activated_skills = _extract_activated_skills(output.get("trace", {}))
    assertion_results: list[dict[str, Any]] = []
    for required_skill in case.required_skill_activations:
        passed = required_skill in activated_skills
        if passed:
            evidence = (
                f"Trace shows activate_skill for '{required_skill}': "
                + ", ".join(sorted(activated_skills))
            )
        else:
            evidence = (
                f"Trace did not show activate_skill for '{required_skill}'. "
                f"Observed activations: {', '.join(sorted(activated_skills)) or 'none'}."
            )
        assertion_results.append(
            {
                "text": f"The trace activates skill '{required_skill}'",
                "passed": passed,
                "evidence": evidence,
                "category": "trigger",
                "weight": 1.0,
            }
        )

    return {
        "assertion_results": assertion_results,
        "summary": _build_grading_summary(assertion_results),
        "category_scores": _build_category_scores(assertion_results),
        "mode": "trace_requirements",
    }


def _extract_activated_skills(trace: dict[str, Any]) -> set[str]:
    activated_skills: set[str] = set()
    for item in trace.get("items", []) or []:
        summary = str((item or {}).get("summary") or "")
        prefix = "function_call:activate_skill:"
        if summary.startswith(prefix):
            activated_skills.add(summary[len(prefix):].strip())
    return activated_skills


def _empty_grading_payload(*, mode: str) -> dict[str, Any]:
    return {
        "assertion_results": [],
        "summary": _build_grading_summary([]),
        "category_scores": {},
        "mode": mode,
    }


def _align_grading_payload(
    *,
    checks: list[EvalCheck],
    payload: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    raw_results = list(payload.get("assertion_results", []) or [])
    matched_results = _match_grading_results(checks=checks, raw_results=raw_results)
    aligned_results: list[dict[str, Any]] = []
    for index, check in enumerate(checks):
        raw_result = matched_results[index]
        aligned_results.append(
            {
                "text": check.text,
                "passed": bool(raw_result.get("passed", False)),
                "evidence": str(
                    raw_result.get("evidence")
                    or "The grader did not return a result for this check."
                ),
                "category": check.category,
                "weight": check.weight,
            }
        )

    return {
        "assertion_results": aligned_results,
        "summary": _build_grading_summary(aligned_results),
        "category_scores": _build_category_scores(aligned_results),
        "mode": mode,
    }


def _match_grading_results(
    *,
    checks: list[EvalCheck],
    raw_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    matched: list[dict[str, Any]] = [{} for _ in checks]
    used_raw_indexes: set[int] = set()

    # First prefer exact text matches.
    for check_index, check in enumerate(checks):
        for raw_index, raw_result in enumerate(raw_results):
            if raw_index in used_raw_indexes:
                continue
            text = str((raw_result or {}).get("text") or "").strip()
            if text == check.text:
                matched[check_index] = dict(raw_result)
                used_raw_indexes.add(raw_index)
                break

    # Then recover paraphrased outputs via conservative fuzzy matching.
    for check_index, check in enumerate(checks):
        if matched[check_index]:
            continue
        best_raw_index: int | None = None
        best_score = 0.0
        for raw_index, raw_result in enumerate(raw_results):
            if raw_index in used_raw_indexes:
                continue
            text = str((raw_result or {}).get("text") or "").strip()
            if not text:
                continue
            score = _grading_text_similarity(check.text, text)
            if score > best_score:
                best_score = score
                best_raw_index = raw_index
        if best_raw_index is not None and best_score >= 0.55:
            matched[check_index] = dict(raw_results[best_raw_index])
            used_raw_indexes.add(best_raw_index)

    # Finally, if the grader returned one result per check in order but with weak text
    # fidelity, align any remaining unmatched items by position.
    if len(raw_results) == len(checks):
        for check_index, raw_result in enumerate(raw_results):
            if matched[check_index]:
                continue
            if check_index in used_raw_indexes:
                continue
            matched[check_index] = dict(raw_result)
            used_raw_indexes.add(check_index)

    return matched


def _grading_text_similarity(expected: str, actual: str) -> float:
    expected_text = " ".join(expected.lower().split())
    actual_text = " ".join(actual.lower().split())
    if not expected_text or not actual_text:
        return 0.0
    return SequenceMatcher(a=expected_text, b=actual_text).ratio()


def _merge_grading_payloads(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    primary_results = list(primary.get("assertion_results", []) or [])
    secondary_results = list(secondary.get("assertion_results", []) or [])
    assertion_results = primary_results + secondary_results
    modes = [mode for mode in [primary.get("mode"), secondary.get("mode")] if mode]
    return {
        "assertion_results": assertion_results,
        "summary": _build_grading_summary(assertion_results),
        "category_scores": _build_category_scores(assertion_results),
        "mode": "+".join(modes) if modes else "merged",
    }


def _build_grading_summary(assertion_results: list[dict[str, Any]]) -> dict[str, Any]:
    passed = sum(1 for result in assertion_results if result.get("passed"))
    total = len(assertion_results)
    failed = total - passed
    pass_rate = 0.0 if total == 0 else passed / total
    total_weight = sum(float(result.get("weight", 1.0) or 1.0) for result in assertion_results)
    passed_weight = sum(
        float(result.get("weight", 1.0) or 1.0)
        for result in assertion_results
        if result.get("passed")
    )
    weighted_pass_rate = 0.0 if total_weight == 0 else passed_weight / total_weight
    return {
        "passed": passed,
        "failed": failed,
        "total": total,
        "pass_rate": pass_rate,
        "weighted_pass_rate": weighted_pass_rate,
    }


def _build_category_scores(assertion_results: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    category_scores: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "passed": 0,
            "failed": 0,
            "total": 0,
            "passed_weight": 0.0,
            "total_weight": 0.0,
            "score": 0.0,
        }
    )
    for result in assertion_results:
        category = str(result.get("category") or "goal")
        weight = float(result.get("weight", 1.0) or 1.0)
        category_scores[category]["total"] += 1
        category_scores[category]["total_weight"] += weight
        if result.get("passed"):
            category_scores[category]["passed"] += 1
            category_scores[category]["passed_weight"] += weight
        else:
            category_scores[category]["failed"] += 1

    for category, values in category_scores.items():
        total_weight = float(values["total_weight"])
        values["score"] = 0.0 if total_weight == 0 else float(values["passed_weight"]) / total_weight
        category_scores[category] = dict(values)
    return dict(category_scores)


def _build_case_comparison(
    *,
    with_skill: dict[str, Any],
    baseline: dict[str, Any],
    baseline_label: str,
) -> dict[str, Any]:
    goal_score_delta = _task_category_delta(with_skill, baseline, "goal")
    evidence_score_delta = _task_category_delta(with_skill, baseline, "evidence")
    format_score_delta = _task_category_delta(with_skill, baseline, "format")
    trigger_score_delta = _task_category_delta(with_skill, baseline, "trigger")
    task_uplift_score = _task_uplift_score(
        category_deltas={
            "goal": goal_score_delta,
            "evidence": evidence_score_delta,
        }
    )
    winner = _comparison_winner(task_uplift_score=task_uplift_score, baseline_label=baseline_label)
    confidence = _comparison_confidence(task_uplift_score)
    cost_delta = {
        "duration_ms": _timing_value(with_skill, "duration_ms") - _timing_value(baseline, "duration_ms"),
        "tokens": _timing_value(with_skill, "total_tokens") - _timing_value(baseline, "total_tokens"),
        "requests": _timing_value(with_skill, "requests") - _timing_value(baseline, "requests"),
    }
    reason = _build_comparison_reason(
        winner=winner,
        baseline_label=baseline_label,
        goal_score_delta=goal_score_delta,
        evidence_score_delta=evidence_score_delta,
        format_score_delta=format_score_delta,
        trigger_score_delta=trigger_score_delta,
    )
    return {
        "baseline_label": baseline_label,
        "winner": winner,
        "confidence": confidence,
        "reason": reason,
        "task_uplift_score": task_uplift_score,
        "goal_score_delta": goal_score_delta,
        "evidence_score_delta": evidence_score_delta,
        "format_score_delta": format_score_delta,
        "trigger_score_delta": trigger_score_delta,
        "cost_delta": cost_delta,
    }


def _task_category_delta(with_skill: dict[str, Any], baseline: dict[str, Any], category: str) -> float:
    return _category_score(with_skill, category) - _category_score(baseline, category)


def _category_score(config_result: dict[str, Any], category: str) -> float:
    category_scores = config_result.get("category_scores", {}) or {}
    category_payload = category_scores.get(category, {}) or {}
    return float(category_payload.get("score", 0.0) or 0.0)


def _task_uplift_score(*, category_deltas: dict[str, float]) -> float:
    available = [category_deltas[category] for category in TASK_UPLIFT_CATEGORIES if category in category_deltas]
    if not available:
        return 0.0
    return float(statistics.mean(available))


def _comparison_winner(*, task_uplift_score: float, baseline_label: str) -> str:
    if task_uplift_score > 0.05:
        return "with_skill"
    if task_uplift_score < -0.05:
        return baseline_label
    return "tie"


def _comparison_confidence(task_uplift_score: float) -> str:
    magnitude = abs(task_uplift_score)
    if magnitude >= 0.5:
        return "high"
    if magnitude >= 0.2:
        return "medium"
    return "low"


def _build_comparison_reason(
    *,
    winner: str,
    baseline_label: str,
    goal_score_delta: float,
    evidence_score_delta: float,
    format_score_delta: float,
    trigger_score_delta: float,
) -> str:
    leader = "with_skill" if winner == "with_skill" else baseline_label if winner == baseline_label else "Neither"
    return (
        f"{leader} led on task-relevant checks. "
        f"goal={goal_score_delta:+.2f}, evidence={evidence_score_delta:+.2f}, "
        f"format={format_score_delta:+.2f}, trigger={trigger_score_delta:+.2f} "
        f"(positive favors with_skill)."
    )


def _timing_value(config_result: dict[str, Any], key: str) -> int:
    timing = config_result.get("timing", {}) or {}
    return int(timing.get(key, 0) or 0)


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
            "weighted_pass_rate": float(summary.get("weighted_pass_rate", 0.0) or 0.0),
        },
        "category_scores": payload.get("category_scores") or {},
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
    labels = sorted({label for case in case_summaries for label in case["configurations"]})
    run_summary: dict[str, Any] = {}
    category_scores: dict[str, dict[str, dict[str, float]]] = {}
    for label in labels:
        pass_rates = [
            case["configurations"][label]["pass_rate"]
            for case in case_summaries
            if label in case["configurations"]
        ]
        weighted_pass_rates = [
            case["configurations"][label]["weighted_pass_rate"]
            for case in case_summaries
            if label in case["configurations"]
        ]
        durations = [
            _timing_value(case["configurations"][label], "duration_ms")
            for case in case_summaries
            if label in case["configurations"]
        ]
        tokens = [
            _timing_value(case["configurations"][label], "total_tokens")
            for case in case_summaries
            if label in case["configurations"]
        ]
        requests = [
            _timing_value(case["configurations"][label], "requests")
            for case in case_summaries
            if label in case["configurations"]
        ]
        run_summary[label] = {
            "pass_rate": _stats(pass_rates),
            "weighted_pass_rate": _stats(weighted_pass_rates),
            "duration_ms": _stats(durations),
            "tokens": _stats(tokens),
            "requests": _stats(requests),
        }
        category_scores[label] = _category_stats_for_label(case_summaries, label)

    if "with_skill" in run_summary:
        baseline_label = "old_skill" if "old_skill" in run_summary else "without_skill"
        if baseline_label in run_summary:
            run_summary["delta"] = {
                "pass_rate": run_summary["with_skill"]["pass_rate"]["mean"]
                - run_summary[baseline_label]["pass_rate"]["mean"],
                "weighted_pass_rate": run_summary["with_skill"]["weighted_pass_rate"]["mean"]
                - run_summary[baseline_label]["weighted_pass_rate"]["mean"],
                "duration_ms": run_summary["with_skill"]["duration_ms"]["mean"]
                - run_summary[baseline_label]["duration_ms"]["mean"],
                "tokens": run_summary["with_skill"]["tokens"]["mean"]
                - run_summary[baseline_label]["tokens"]["mean"],
                "requests": run_summary["with_skill"]["requests"]["mean"]
                - run_summary[baseline_label]["requests"]["mean"],
                "baseline": baseline_label,
            }

    benchmark: dict[str, Any] = {
        "run_summary": run_summary,
        "category_scores": category_scores,
    }
    comparison_summary = _build_comparison_summary(case_summaries)
    if comparison_summary is not None:
        benchmark["comparison_summary"] = comparison_summary
        benchmark["with_skill_win_rate"] = comparison_summary["with_skill_win_rate"]
        benchmark["task_uplift_score"] = comparison_summary["task_uplift_score"]
        benchmark["category_deltas"] = comparison_summary["category_deltas"]
        benchmark["cost_deltas"] = comparison_summary["cost_deltas"]
        benchmark["promotion_signal"] = comparison_summary["promotion_signal"]
    return benchmark


def _category_stats_for_label(
    case_summaries: list[dict[str, Any]],
    label: str,
) -> dict[str, dict[str, float]]:
    category_values: dict[str, list[float]] = defaultdict(list)
    for case in case_summaries:
        config = case["configurations"].get(label)
        if config is None:
            continue
        for category, payload in (config.get("category_scores", {}) or {}).items():
            category_values[category].append(float((payload or {}).get("score", 0.0) or 0.0))
    return {category: _stats(values) for category, values in category_values.items()}


def _build_comparison_summary(case_summaries: list[dict[str, Any]]) -> dict[str, Any] | None:
    comparisons = [case.get("comparison") for case in case_summaries if case.get("comparison") is not None]
    if not comparisons:
        return None

    baseline_label = str(comparisons[0]["baseline_label"])
    winners = [str(comparison["winner"]) for comparison in comparisons]
    with_skill_win_rate = winners.count("with_skill") / len(winners)
    baseline_win_rate = winners.count(baseline_label) / len(winners)
    tie_rate = winners.count("tie") / len(winners)
    category_deltas = {
        "goal": float(statistics.mean([float(item["goal_score_delta"]) for item in comparisons])),
        "evidence": float(statistics.mean([float(item["evidence_score_delta"]) for item in comparisons])),
        "format": float(statistics.mean([float(item["format_score_delta"]) for item in comparisons])),
        "trigger": float(statistics.mean([float(item["trigger_score_delta"]) for item in comparisons])),
    }
    task_uplift_score = _task_uplift_score(category_deltas=category_deltas)
    cost_deltas = {
        "duration_ms": float(statistics.mean([float(item["cost_delta"]["duration_ms"]) for item in comparisons])),
        "tokens": float(statistics.mean([float(item["cost_delta"]["tokens"]) for item in comparisons])),
        "requests": float(statistics.mean([float(item["cost_delta"]["requests"]) for item in comparisons])),
    }
    promotion_successful = with_skill_win_rate > baseline_win_rate and task_uplift_score > 0.0
    promotion_reason = (
        "with_skill beat baseline on task-relevant checks."
        if promotion_successful
        else "with_skill did not clearly beat baseline on task-relevant checks."
    )
    return {
        "baseline_label": baseline_label,
        "total_cases": len(comparisons),
        "with_skill_win_rate": with_skill_win_rate,
        "baseline_win_rate": baseline_win_rate,
        "tie_rate": tie_rate,
        "task_uplift_score": task_uplift_score,
        "category_deltas": category_deltas,
        "cost_deltas": cost_deltas,
        "promotion_signal": {
            "successful": promotion_successful,
            "reason": promotion_reason,
        },
    }


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
