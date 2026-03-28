from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .models import EvalCheck, Skill, SkillEvalCase, SkillEvalSuite

ALLOWED_CHECK_CATEGORIES = {"goal", "evidence", "format", "trigger"}


def load_skill_eval_suite(skill: Skill) -> SkillEvalSuite | None:
    evals_path = skill.path / "evals" / "evals.json"
    if not evals_path.is_file():
        return None

    payload = json.loads(evals_path.read_text(encoding="utf-8"))
    raw_cases = payload.get("evals") or []
    if not isinstance(raw_cases, list):
        raise ValueError(f"Invalid evals payload in {evals_path}: 'evals' must be a list.")

    cases: list[SkillEvalCase] = []
    for index, raw_case in enumerate(raw_cases, start=1):
        if not isinstance(raw_case, dict):
            raise ValueError(
                f"Invalid eval case #{index} in {evals_path}: each case must be an object."
            )
        prompt = str(raw_case.get("prompt") or "").strip()
        expected_output = str(raw_case.get("expected_output") or "").strip()
        if not prompt or not expected_output:
            raise ValueError(
                f"Invalid eval case #{index} in {evals_path}: prompt and expected_output are required."
            )

        raw_id = raw_case.get("id")
        case_id = _normalize_case_id(raw_id, fallback=f"case-{index}")
        files = [Path(str(item)) for item in raw_case.get("files") or []]
        checks = _load_eval_checks(raw_case, evals_path=evals_path, case_id=case_id)
        required_skill_activations = [
            str(item) for item in raw_case.get("required_skill_activations") or []
        ]
        cases.append(
            SkillEvalCase(
                case_id=case_id,
                prompt=prompt,
                expected_output=expected_output,
                files=files,
                checks=checks,
                required_skill_activations=required_skill_activations,
            )
        )

    return SkillEvalSuite(
        skill_name=str(payload.get("skill_name") or skill.name),
        evals_path=evals_path,
        cases=cases,
    )


def resolve_eval_case_files(skill: Skill, case: SkillEvalCase) -> list[Path]:
    resolved_paths: list[Path] = []
    skill_root = skill.path.resolve()
    for relative_path in case.files:
        resolved = (skill.path / relative_path).resolve()
        try:
            resolved.relative_to(skill_root)
        except ValueError as exc:
            raise ValueError(
                f"Eval file '{relative_path.as_posix()}' escapes skill directory for {skill.name}."
            ) from exc
        if not resolved.is_file():
            raise FileNotFoundError(
                f"Eval file not found for skill {skill.name}: {relative_path.as_posix()}"
            )
        resolved_paths.append(resolved)
    return resolved_paths


def next_iteration_dir(skill: Skill) -> Path:
    workspace_root = skill.path / "evals" / "workspace"
    workspace_root.mkdir(parents=True, exist_ok=True)
    existing = sorted(
        child
        for child in workspace_root.iterdir()
        if child.is_dir() and re.fullmatch(r"iteration-\d+", child.name)
    )
    next_index = 1
    if existing:
        next_index = max(int(path.name.split("-")[1]) for path in existing) + 1
    iteration_dir = workspace_root / f"iteration-{next_index}"
    iteration_dir.mkdir(parents=True, exist_ok=True)
    return iteration_dir


def snapshot_skill(skill: Skill, destination_root: Path) -> Path:
    snapshot_root = destination_root / "skill-snapshot"
    snapshot_root.mkdir(parents=True, exist_ok=True)
    snapshot_dir = snapshot_root / skill.name
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
    shutil.copytree(
        skill.path,
        snapshot_dir,
        ignore=shutil.ignore_patterns("workspace"),
    )
    return snapshot_dir


def _normalize_case_id(raw_id: object, *, fallback: str) -> str:
    candidate = str(raw_id or fallback).strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", candidate).strip("-")
    return normalized or fallback


def _load_eval_checks(raw_case: dict[str, object], *, evals_path: Path, case_id: str) -> list[EvalCheck]:
    raw_checks = raw_case.get("checks")
    if raw_checks is not None:
        if not isinstance(raw_checks, list):
            raise ValueError(
                f"Invalid eval case '{case_id}' in {evals_path}: 'checks' must be a list."
            )
        checks: list[EvalCheck] = []
        for index, raw_check in enumerate(raw_checks, start=1):
            if not isinstance(raw_check, dict):
                raise ValueError(
                    f"Invalid check #{index} for eval case '{case_id}' in {evals_path}: "
                    "each check must be an object."
                )
            text = str(raw_check.get("text") or "").strip()
            category = str(raw_check.get("category") or "goal").strip().lower()
            try:
                weight = float(raw_check.get("weight", 1.0) or 1.0)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Invalid check #{index} for eval case '{case_id}' in {evals_path}: "
                    "'weight' must be numeric."
                ) from exc
            if not text:
                raise ValueError(
                    f"Invalid check #{index} for eval case '{case_id}' in {evals_path}: "
                    "'text' is required."
                )
            if category not in ALLOWED_CHECK_CATEGORIES:
                allowed = ", ".join(sorted(ALLOWED_CHECK_CATEGORIES))
                raise ValueError(
                    f"Invalid check #{index} for eval case '{case_id}' in {evals_path}: "
                    f"'category' must be one of {allowed}."
                )
            if weight <= 0:
                raise ValueError(
                    f"Invalid check #{index} for eval case '{case_id}' in {evals_path}: "
                    "'weight' must be positive."
                )
            checks.append(EvalCheck(text=text, category=category, weight=weight))
        return checks

    return [
        EvalCheck(text=str(item), category="goal", weight=1.0)
        for item in raw_case.get("assertions") or []
    ]
