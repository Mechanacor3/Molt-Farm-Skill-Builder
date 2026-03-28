from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from . import runner
from .models import AgentDefinition, Skill
from .runner import execute_task
from .skill_loader import discover_skills
from .storage import write_json, write_text

ALLOWED_FIXTURE_EXTENSIONS = {".json", ".md", ".markdown", ".txt"}
ALLOWED_CHECK_CATEGORIES = {"goal", "evidence", "format", "trigger"}


class SuggestedFlavor(BaseModel):
    id: str
    title: str
    rationale: str
    recommended: bool = False
    evidence: list[str] = Field(default_factory=list)
    fixture_strategy: str


class SuggestedFlavorPayload(BaseModel):
    suggested_flavors: list[SuggestedFlavor] = Field(default_factory=list)


class DraftFixture(BaseModel):
    path: str
    content: str


class DraftCheck(BaseModel):
    text: str
    category: str = "goal"
    weight: float = 1.0


class DraftEvalCase(BaseModel):
    id: str
    prompt: str
    expected_output: str
    files: list[str] = Field(default_factory=list)
    checks: list[DraftCheck] = Field(default_factory=list)
    required_skill_activations: list[str] = Field(default_factory=list)


class DraftSuitePayload(BaseModel):
    evals: list[DraftEvalCase] = Field(default_factory=list)
    fixtures: list[DraftFixture] = Field(default_factory=list)
    preview_markdown: str = ""


def create_evals(
    project_root: Path,
    *,
    skill_name: str,
    session_id: str | None = None,
    answers: dict[str, str] | None = None,
    promote: bool = False,
    model: str = "gpt-5",
) -> dict[str, Any]:
    answers = answers or {}
    skills_by_name = discover_skills(project_root / "skills")
    skill = skills_by_name.get(skill_name)
    if skill is None:
        raise ValueError(f"Unknown skill '{skill_name}'.")

    if session_id is None:
        if promote:
            raise ValueError("Promotion requires --session <session-id>.")
        if answers:
            raise ValueError("Answers require --session <session-id>.")
        return _start_new_session(project_root=project_root, skill=skill, model=model)

    session_dir = _resolve_session_dir(skill, session_id=session_id)
    session = _load_session_state(session_dir)
    if session.get("skill_name") != skill.name:
        raise ValueError(
            f"Session '{session_id}' belongs to skill '{session.get('skill_name')}', not '{skill.name}'."
        )

    if session.get("phase") == "promoted":
        if answers or promote:
            raise ValueError(f"Session '{session_id}' has already been promoted.")
        return _build_session_response(project_root=project_root, skill=skill, session=session)

    should_build_draft = False
    if answers:
        _apply_answers(session, answers)
        should_build_draft = bool(session.get("selected_flavors"))
        _write_session_state(session_dir, session)

    if should_build_draft or (
        session.get("phase") == "awaiting_selection" and session.get("selected_flavors")
    ):
        _build_draft_for_session(
            project_root=project_root,
            skill=skill,
            session=session,
            session_dir=session_dir,
            model=model,
        )

    if promote:
        if session.get("phase") != "draft_ready":
            raise ValueError(
                f"Session '{session_id}' is in phase '{session.get('phase')}' and cannot be promoted yet."
            )
        promotion = _promote_draft(
            project_root=project_root,
            skill=skill,
            session=session,
            session_dir=session_dir,
        )
        session["phase"] = "promoted"
        session["status"] = "completed"
        session["promotion_backup_path"] = promotion["promotion_backup_path"]
        session["promoted_evals_path"] = promotion["promoted_evals_path"]
        session["copied_fixture_paths"] = promotion["copied_fixture_paths"]
        _write_session_state(session_dir, session)

    return _build_session_response(project_root=project_root, skill=skill, session=session)


def _start_new_session(*, project_root: Path, skill: Skill, model: str) -> dict[str, Any]:
    session_dir = _create_session_dir(skill)
    session_id = session_dir.name
    existing_payload = _load_existing_eval_payload(skill)
    skill_profile = _build_skill_profile(project_root=project_root, skill=skill, existing_payload=existing_payload)
    skill_profile_path = write_json(session_dir / "analysis" / "skill-profile.json", skill_profile)

    probe_specs = _build_probe_specs(project_root=project_root, skill=skill, existing_payload=existing_payload)
    probe_payload = _run_probe_suite(
        project_root=project_root,
        skill=skill,
        session_dir=session_dir,
        probe_specs=probe_specs,
        model=model,
    )
    probe_summary_path = write_json(session_dir / "analysis" / "probe-observations.json", probe_payload)

    suggested_flavors = _suggest_flavors(
        project_root=project_root,
        skill=skill,
        skill_profile=skill_profile,
        probe_payload=probe_payload,
        existing_payload=existing_payload,
        model=model,
    )
    suggested_payload = {
        "skill_name": skill.name,
        "session_id": session_id,
        "suggested_flavors": suggested_flavors,
    }
    suggested_flavors_path = write_json(
        session_dir / "analysis" / "suggested-flavors.json",
        suggested_payload,
    )

    session = {
        "session_id": session_id,
        "skill_name": skill.name,
        "phase": "awaiting_selection",
        "status": "awaiting_input",
        "selected_flavors": [],
        "author_notes": "",
        "skill_profile_path": _relative_to_project(project_root, skill_profile_path),
        "probe_summary_path": _relative_to_project(project_root, probe_summary_path),
        "suggested_flavors_path": _relative_to_project(project_root, suggested_flavors_path),
        "draft_evals_path": None,
        "draft_preview_path": None,
        "draft_fixture_dir": None,
        "promotion_backup_path": None,
        "promoted_evals_path": None,
        "generated_case_ids": [],
        "generated_fixture_paths": [],
        "copied_fixture_paths": [],
    }
    _write_session_state(session_dir, session)
    return _build_session_response(project_root=project_root, skill=skill, session=session)


def _build_draft_for_session(
    *,
    project_root: Path,
    skill: Skill,
    session: dict[str, Any],
    session_dir: Path,
    model: str,
) -> None:
    selected_flavors = list(session.get("selected_flavors") or [])
    if not selected_flavors:
        session["phase"] = "awaiting_selection"
        session["status"] = "awaiting_input"
        _write_session_state(session_dir, session)
        return

    suggested_payload = _read_json(project_root / str(session["suggested_flavors_path"]))
    suggested_flavors = list(suggested_payload.get("suggested_flavors") or [])
    known_flavor_ids = {str(flavor.get("id") or "") for flavor in suggested_flavors}
    unknown_flavors = [flavor_id for flavor_id in selected_flavors if flavor_id not in known_flavor_ids]
    if unknown_flavors:
        raise ValueError(
            "Unknown selected flavor ids: " + ", ".join(sorted(unknown_flavors))
        )

    existing_payload = _load_existing_eval_payload(skill)
    skill_profile = _read_json(project_root / str(session["skill_profile_path"]))
    probe_payload = _read_json(project_root / str(session["probe_summary_path"]))
    draft_payload = _draft_eval_suite(
        project_root=project_root,
        skill=skill,
        session=session,
        skill_profile=skill_profile,
        probe_payload=probe_payload,
        suggested_flavors=suggested_flavors,
        existing_payload=existing_payload,
        model=model,
    )
    materialized = _materialize_draft(
        project_root=project_root,
        skill=skill,
        session=session,
        session_dir=session_dir,
        draft_payload=draft_payload,
        existing_payload=existing_payload,
    )
    session["phase"] = "draft_ready"
    session["status"] = "active"
    session["draft_evals_path"] = materialized["draft_evals_path"]
    session["draft_preview_path"] = materialized["draft_preview_path"]
    session["draft_fixture_dir"] = materialized["draft_fixture_dir"]
    session["generated_case_ids"] = materialized["generated_case_ids"]
    session["generated_fixture_paths"] = materialized["generated_fixture_paths"]
    _write_session_state(session_dir, session)


def _promote_draft(
    *,
    project_root: Path,
    skill: Skill,
    session: dict[str, Any],
    session_dir: Path,
) -> dict[str, Any]:
    draft_evals_path = session.get("draft_evals_path")
    draft_fixture_dir = session.get("draft_fixture_dir")
    if not isinstance(draft_evals_path, str) or not draft_evals_path:
        raise ValueError("Draft eval suite is not available for promotion.")
    if not isinstance(draft_fixture_dir, str) or not draft_fixture_dir:
        raise ValueError("Draft fixture directory is not available for promotion.")

    canonical_evals_path = skill.path / "evals" / "evals.json"
    canonical_files_dir = skill.path / "evals" / "files"
    promotion_dir = session_dir / "promotion"
    promotion_dir.mkdir(parents=True, exist_ok=True)

    previous_evals_path: str | None = None
    if canonical_evals_path.is_file():
        backup_path = promotion_dir / "previous-evals.json"
        shutil.copyfile(canonical_evals_path, backup_path)
        previous_evals_path = _relative_to_project(project_root, backup_path)

    promoted_payload = _read_json(project_root / draft_evals_path)
    write_json(canonical_evals_path, promoted_payload)

    copied_fixture_paths: list[str] = []
    draft_files_root = project_root / draft_fixture_dir
    if draft_files_root.exists():
        for source_path in sorted(path for path in draft_files_root.rglob("*") if path.is_file()):
            relative = source_path.relative_to(draft_files_root)
            destination_path = canonical_files_dir / relative
            destination_path.parent.mkdir(parents=True, exist_ok=True)
            if destination_path.exists():
                source_content = source_path.read_text(encoding="utf-8")
                destination_content = destination_path.read_text(encoding="utf-8")
                if source_content != destination_content:
                    raise ValueError(
                        f"Refusing to overwrite existing fixture during promotion: {destination_path}"
                    )
            else:
                shutil.copyfile(source_path, destination_path)
            copied_fixture_paths.append(_relative_to_project(project_root, destination_path))

    return {
        "promotion_backup_path": previous_evals_path,
        "promoted_evals_path": _relative_to_project(project_root, canonical_evals_path),
        "copied_fixture_paths": copied_fixture_paths,
    }


def _draft_eval_suite(
    *,
    project_root: Path,
    skill: Skill,
    session: dict[str, Any],
    skill_profile: dict[str, Any],
    probe_payload: dict[str, Any],
    suggested_flavors: list[dict[str, Any]],
    existing_payload: dict[str, Any],
    model: str,
) -> dict[str, Any]:
    eval_author_skill = _load_eval_author_skill(project_root)
    sdk = _load_sdk(project_root)
    agent = sdk.Agent(
        name="eval-author-suite-drafter",
        model=model,
        instructions=(
            f"{eval_author_skill.instructions}\n\n"
            "Produce additive draft eval cases and any new fixture files needed for the selected flavors. "
            "Return JSON only. Do not repeat existing canonical eval cases; only propose newly generated cases "
            "plus new draft fixtures."
        ),
        output_type=DraftSuitePayload,
    )
    prompt = _build_draft_prompt(
        skill=skill,
        session=session,
        skill_profile=skill_profile,
        probe_payload=probe_payload,
        suggested_flavors=suggested_flavors,
        existing_payload=existing_payload,
    )
    result = sdk.Runner.run_sync(agent, prompt)
    return _normalize_draft_payload(
        skill=skill,
        session=session,
        existing_payload=existing_payload,
        selected_flavors=list(session.get("selected_flavors") or []),
        suggested_flavors=suggested_flavors,
        payload=_coerce_draft_payload(result.final_output),
    )


def _suggest_flavors(
    *,
    project_root: Path,
    skill: Skill,
    skill_profile: dict[str, Any],
    probe_payload: dict[str, Any],
    existing_payload: dict[str, Any],
    model: str,
) -> list[dict[str, Any]]:
    eval_author_skill = _load_eval_author_skill(project_root)
    sdk = _load_sdk(project_root)
    agent = sdk.Agent(
        name="eval-author-flavor-suggester",
        model=model,
        instructions=(
            f"{eval_author_skill.instructions}\n\n"
            "Suggest three to five additive eval flavors for the target skill. "
            "Return JSON only. Each flavor must have id, title, rationale, recommended, evidence, and fixture_strategy."
        ),
        output_type=SuggestedFlavorPayload,
    )
    prompt = _build_flavor_prompt(
        skill_profile=skill_profile,
        probe_payload=probe_payload,
        existing_payload=existing_payload,
    )
    result = sdk.Runner.run_sync(agent, prompt)
    return _normalize_suggested_flavors(
        payload=_coerce_suggested_flavor_payload(result.final_output),
        existing_payload=existing_payload,
        probe_payload=probe_payload,
    )


def _run_probe_suite(
    *,
    project_root: Path,
    skill: Skill,
    session_dir: Path,
    probe_specs: list[dict[str, Any]],
    model: str,
) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    for probe_spec in probe_specs:
        probe_dir = session_dir / "probes" / f"probe-{probe_spec['probe_id']}"
        write_json(probe_dir / "prompt.json", probe_spec)
        with_skill = _run_probe_configuration(
            project_root=project_root,
            skill=skill,
            probe_dir=probe_dir,
            probe_spec=probe_spec,
            label="with_skill",
            configured_skill=skill,
            model=model,
        )
        without_skill = _run_probe_configuration(
            project_root=project_root,
            skill=skill,
            probe_dir=probe_dir,
            probe_spec=probe_spec,
            label="without_skill",
            configured_skill=None,
            model=model,
        )
        observations.append(
            {
                "probe_id": probe_spec["probe_id"],
                "prompt": probe_spec["prompt"],
                "files": list(probe_spec.get("files") or []),
                "with_skill": with_skill,
                "without_skill": without_skill,
            }
        )
    return {
        "skill_name": skill.name,
        "probes": observations,
    }


def _run_probe_configuration(
    *,
    project_root: Path,
    skill: Skill,
    probe_dir: Path,
    probe_spec: dict[str, Any],
    label: str,
    configured_skill: Skill | None,
    model: str,
) -> dict[str, Any]:
    config_dir = probe_dir / label
    task_input: dict[str, Any] = {"task": str(probe_spec["prompt"])}
    for index, relative_path in enumerate(probe_spec.get("files") or [], start=1):
        task_input[f"input_file_{index}"] = relative_path

    agent = AgentDefinition(
        name=f"{skill.name}-eval-author-probe",
        description=f"Probe worker for drafting evals for {skill.name}.",
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
    write_text(config_dir / "summary.txt", output.get("summary", ""))
    write_json(config_dir / "timing.json", _build_timing_payload(output))
    write_json(config_dir / "trace.json", output.get("trace", {}))
    return {
        "status": status,
        "summary": output.get("summary", ""),
        "result_path": _relative_to_project(project_root, config_dir / "result.json"),
        "summary_path": _relative_to_project(project_root, config_dir / "summary.txt"),
        "timing_path": _relative_to_project(project_root, config_dir / "timing.json"),
        "trace_path": _relative_to_project(project_root, config_dir / "trace.json"),
        "timing": _build_timing_payload(output),
    }


def _build_skill_profile(
    *,
    project_root: Path,
    skill: Skill,
    existing_payload: dict[str, Any],
) -> dict[str, Any]:
    skill_file = skill.path / "SKILL.md"
    evals_path = skill.path / "evals" / "evals.json"
    latest_iteration = _find_latest_iteration_dir(skill)
    relevant_lessons = _find_relevant_lessons(project_root=project_root, skill=skill)
    existing_cases = [
        case
        for case in list(existing_payload.get("evals") or [])
        if isinstance(case, dict)
    ]

    profile = {
        "skill_name": skill.name,
        "description": skill.description,
        "skill_path": _relative_to_project(project_root, skill.path),
        "skill_file_path": _relative_to_project(project_root, skill_file),
        "skill_instructions": skill.instructions,
        "referenced_paths": [path.as_posix() for path in skill.referenced_paths],
        "resource_paths": [
            path.as_posix()
            for _, paths in skill.resources.iter_categories()
            for path in paths
            if "evals/workspace/" not in path.as_posix()
        ],
        "existing_evals_path": _relative_to_project(project_root, evals_path) if evals_path.is_file() else None,
        "existing_eval_count": len(existing_cases),
        "existing_eval_case_ids": [str(case.get("id") or "") for case in existing_cases],
        "existing_evals_excerpt": _read_text_excerpt(evals_path) if evals_path.is_file() else "",
        "relevant_lessons": relevant_lessons,
        "latest_iteration_path": _relative_to_project(project_root, latest_iteration) if latest_iteration else None,
        "latest_iteration_benchmark_excerpt": _read_text_excerpt(latest_iteration / "benchmark.json") if latest_iteration and (latest_iteration / "benchmark.json").is_file() else "",
        "latest_iteration_feedback_excerpt": _read_text_excerpt(latest_iteration / "feedback.json") if latest_iteration and (latest_iteration / "feedback.json").is_file() else "",
        "latest_iteration_comparisons": _read_iteration_artifacts(project_root=project_root, iteration_dir=latest_iteration, pattern="eval-*/comparison.json"),
        "latest_iteration_traces": _read_iteration_artifacts(project_root=project_root, iteration_dir=latest_iteration, pattern="eval-*/with_skill/trace.json"),
    }
    return profile


def _build_probe_specs(
    *,
    project_root: Path,
    skill: Skill,
    existing_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    used_prompts: set[str] = set()
    raw_cases = [
        case
        for case in list(existing_payload.get("evals") or [])
        if isinstance(case, dict)
    ]

    for index, raw_case in enumerate(raw_cases[:2], start=1):
        prompt = str(raw_case.get("prompt") or "").strip()
        if not prompt or prompt in used_prompts:
            continue
        probe_id = _normalize_slug(str(raw_case.get("id") or f"existing-{index}"))
        specs.append(
            {
                "probe_id": probe_id,
                "prompt": prompt,
                "files": _resolve_existing_case_files(
                    project_root=project_root,
                    skill=skill,
                    raw_case=raw_case,
                ),
                "source": "existing_eval",
            }
        )
        used_prompts.add(prompt)

    generic_prompts = [
        (
            "primary-task",
            f"A user needs help with this skill: {skill.description}. "
            "Give the narrowest useful first response for the most likely real task."
        ),
        (
            "evidence-discipline",
            f"A user asks for help with {skill.name}. "
            "Explain what concrete local evidence or artifact the answer should rely on or name."
        ),
        (
            "next-phase",
            f"The current use of {skill.name} feels broad or unfocused. "
            "What focused next response should the skill produce instead?"
        ),
    ]
    for probe_id, prompt in generic_prompts:
        if len(specs) >= 4:
            break
        if prompt in used_prompts:
            continue
        specs.append({"probe_id": probe_id, "prompt": prompt, "files": [], "source": "generic"})
        used_prompts.add(prompt)

    return specs[: max(2, min(len(specs), 4))]


def _resolve_existing_case_files(
    *,
    project_root: Path,
    skill: Skill,
    raw_case: dict[str, Any],
) -> list[str]:
    resolved: list[str] = []
    for item in list(raw_case.get("files") or [])[:2]:
        relative_path = str(item).strip()
        if not relative_path:
            continue
        candidate = (skill.path / relative_path).resolve()
        try:
            candidate.relative_to(skill.path.resolve())
        except ValueError:
            continue
        if candidate.is_file():
            resolved.append(_relative_to_project(project_root, candidate))
    return resolved


def _build_flavor_prompt(
    *,
    skill_profile: dict[str, Any],
    probe_payload: dict[str, Any],
    existing_payload: dict[str, Any],
) -> str:
    lines = [
        "Draft additive eval coverage for a local skill.",
        "Use the skill profile, existing evals, and the with-skill versus without-skill probe results.",
        "Favor realistic local prompts, goal/evidence checks, and inspectable fixtures.",
        "",
        "Skill profile JSON:",
        json.dumps(skill_profile, indent=2),
        "",
        "Existing evals JSON:",
        json.dumps(existing_payload, indent=2),
        "",
        "Probe observations JSON:",
        json.dumps(probe_payload, indent=2),
        "",
        "Return JSON only.",
    ]
    return "\n".join(lines)


def _build_draft_prompt(
    *,
    skill: Skill,
    session: dict[str, Any],
    skill_profile: dict[str, Any],
    probe_payload: dict[str, Any],
    suggested_flavors: list[dict[str, Any]],
    existing_payload: dict[str, Any],
) -> str:
    lines = [
        f"Build additive draft eval cases for skill '{skill.name}'.",
        "Return JSON only.",
        "Create only newly generated cases and any new fixture files they need.",
        "Use plain local fixtures only: Markdown, text, or JSON.",
        "If a new case uses a file, either reference an existing canonical skill-local file or include a new fixture.",
        "",
        f"Selected flavor ids: {', '.join(session.get('selected_flavors') or [])}",
        f"Author notes: {session.get('author_notes') or 'none'}",
        "",
        "Suggested flavors JSON:",
        json.dumps(suggested_flavors, indent=2),
        "",
        "Skill profile JSON:",
        json.dumps(skill_profile, indent=2),
        "",
        "Existing evals JSON:",
        json.dumps(existing_payload, indent=2),
        "",
        "Probe observations JSON:",
        json.dumps(probe_payload, indent=2),
    ]
    return "\n".join(lines)


def _normalize_suggested_flavors(
    *,
    payload: dict[str, Any],
    existing_payload: dict[str, Any],
    probe_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    raw_flavors = list(payload.get("suggested_flavors") or [])
    normalized: list[dict[str, Any]] = []
    used_ids: set[str] = set()
    for index, raw_flavor in enumerate(raw_flavors, start=1):
        if not isinstance(raw_flavor, dict):
            continue
        title = str(raw_flavor.get("title") or "").strip()
        flavor_id = _normalize_slug(str(raw_flavor.get("id") or title or f"flavor-{index}"))
        if not title:
            title = flavor_id.replace("-", " ").title()
        flavor_id = _unique_slug(flavor_id, used_ids)
        used_ids.add(flavor_id)
        evidence = _coerce_evidence_list(raw_flavor.get("evidence"))
        normalized.append(
            {
                "id": flavor_id,
                "title": title,
                "rationale": str(raw_flavor.get("rationale") or "").strip()
                or f"Add coverage for {title.lower()}.",
                "recommended": bool(raw_flavor.get("recommended", False)),
                "evidence": evidence,
                "fixture_strategy": str(raw_flavor.get("fixture_strategy") or "").strip()
                or "Use one narrow local fixture when it materially improves inspectability.",
            }
        )
        if len(normalized) >= 5:
            break

    if len(normalized) < 3:
        for fallback in _fallback_suggested_flavors(existing_payload=existing_payload, probe_payload=probe_payload):
            if fallback["id"] in used_ids:
                continue
            normalized.append(fallback)
            used_ids.add(fallback["id"])
            if len(normalized) >= 3:
                break

    normalized = normalized[:5]
    if normalized and not any(flavor["recommended"] for flavor in normalized):
        normalized[0]["recommended"] = True
    return normalized


def _normalize_draft_payload(
    *,
    skill: Skill,
    session: dict[str, Any],
    existing_payload: dict[str, Any],
    selected_flavors: list[str],
    suggested_flavors: list[dict[str, Any]],
    payload: dict[str, Any],
) -> dict[str, Any]:
    normalized_fixtures, fixture_aliases = _normalize_fixtures(skill=skill, raw_fixtures=payload.get("fixtures"))
    generated_cases = _normalize_generated_cases(
        skill=skill,
        existing_payload=existing_payload,
        raw_cases=payload.get("evals"),
        fixture_aliases=fixture_aliases,
    )
    if not generated_cases:
        generated_cases = _fallback_generated_cases(
            skill=skill,
            selected_flavors=selected_flavors,
            suggested_flavors=suggested_flavors,
            existing_payload=existing_payload,
        )

    merged_payload = json.loads(json.dumps(existing_payload))
    merged_payload["skill_name"] = str(merged_payload.get("skill_name") or skill.name)
    merged_payload["evals"] = list(merged_payload.get("evals") or []) + generated_cases

    preview_markdown = _build_preview_markdown(
        skill=skill,
        session=session,
        existing_payload=existing_payload,
        generated_cases=generated_cases,
        generated_fixtures=normalized_fixtures,
    )
    return {
        "merged_payload": merged_payload,
        "generated_cases": generated_cases,
        "generated_fixtures": normalized_fixtures,
        "preview_markdown": preview_markdown,
    }


def _normalize_generated_cases(
    *,
    skill: Skill,
    existing_payload: dict[str, Any],
    raw_cases: Any,
    fixture_aliases: dict[str, str],
) -> list[dict[str, Any]]:
    existing_case_ids = {
        _normalize_slug(str(case.get("id") or f"case-{index}"))
        for index, case in enumerate(existing_payload.get("evals") or [], start=1)
        if isinstance(case, dict)
    }
    used_case_ids = set(existing_case_ids)
    normalized_cases: list[dict[str, Any]] = []

    for index, raw_case in enumerate(list(raw_cases or []), start=1):
        if not isinstance(raw_case, dict):
            continue
        prompt = str(raw_case.get("prompt") or "").strip()
        expected_output = str(raw_case.get("expected_output") or "").strip()
        if not prompt or not expected_output:
            continue
        case_id = _normalize_slug(str(raw_case.get("id") or f"generated-{index}"))
        case_id = _unique_slug(case_id, used_case_ids)
        used_case_ids.add(case_id)
        files = _normalize_case_files(
            skill=skill,
            raw_files=raw_case.get("files"),
            fixture_aliases=fixture_aliases,
        )
        checks = _normalize_case_checks(raw_case.get("checks"), files=files)
        required_skill_activations = [
            str(item).strip()
            for item in list(raw_case.get("required_skill_activations") or [])
            if str(item).strip()
        ]
        normalized_cases.append(
            {
                "id": case_id,
                "prompt": prompt,
                "expected_output": expected_output,
                "files": files,
                "checks": checks,
                "required_skill_activations": required_skill_activations,
            }
        )
    return normalized_cases


def _normalize_case_checks(raw_checks: Any, *, files: list[str]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for raw_check in list(raw_checks or []):
        if isinstance(raw_check, str):
            text = raw_check.strip()
            if text:
                normalized.append(
                    {
                        "text": text,
                        "category": "goal",
                        "weight": 1.0,
                    }
                )
            continue
        if not isinstance(raw_check, dict):
            continue
        text = str(raw_check.get("text") or "").strip()
        if not text:
            continue
        category = str(raw_check.get("category") or "goal").strip().lower()
        if category not in ALLOWED_CHECK_CATEGORIES:
            category = "goal"
        try:
            weight = float(raw_check.get("weight", 1.0) or 1.0)
        except (TypeError, ValueError):
            weight = 1.0
        if weight <= 0:
            weight = 1.0
        normalized.append(
            {
                "text": text,
                "category": category,
                "weight": weight,
            }
        )

    if normalized:
        return normalized

    fallback_checks = [
        {
            "text": "The answer solves the requested task",
            "category": "goal",
            "weight": 3.0,
        },
        {
            "text": "The answer matches the expected output contract",
            "category": "format",
            "weight": 1.0,
        },
    ]
    if files:
        fallback_checks.insert(
            1,
            {
                "text": "The answer cites or uses the provided artifact when relevant",
                "category": "evidence",
                "weight": 2.0,
            },
        )
    return fallback_checks


def _normalize_case_files(
    *,
    skill: Skill,
    raw_files: Any,
    fixture_aliases: dict[str, str],
) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw_item in list(raw_files or []):
        candidate = str(raw_item).strip().replace("\\", "/")
        if not candidate:
            continue
        resolved = fixture_aliases.get(candidate)
        if resolved is None:
            resolved = fixture_aliases.get(Path(candidate).name)
        if resolved is None and candidate.startswith("evals/files/") and (skill.path / candidate).is_file():
            resolved = candidate
        if resolved is None and (skill.path / candidate).is_file():
            resolved = candidate
        if resolved is None:
            canonical_existing = f"evals/files/{Path(candidate).name}"
            if (skill.path / canonical_existing).is_file():
                resolved = canonical_existing
        if resolved is None or resolved in seen:
            continue
        normalized.append(resolved)
        seen.add(resolved)
    return normalized


def _normalize_fixtures(
    *,
    skill: Skill,
    raw_fixtures: Any,
) -> tuple[list[dict[str, str]], dict[str, str]]:
    normalized: list[dict[str, str]] = []
    aliases: dict[str, str] = {}
    used_paths = {
        path.relative_to(skill.path).as_posix()
        for path in (skill.path / "evals" / "files").rglob("*")
        if path.is_file()
    } if (skill.path / "evals" / "files").exists() else set()

    for index, raw_fixture in enumerate(list(raw_fixtures or []), start=1):
        if not isinstance(raw_fixture, dict):
            continue
        original_path = str(raw_fixture.get("path") or f"generated-{index}.md").strip()
        content = str(raw_fixture.get("content") or "")
        if not content.strip():
            continue
        canonical_path = _sanitize_fixture_path(original_path, index=index)
        canonical_path = _ensure_unique_fixture_path(canonical_path, used_paths)
        used_paths.add(canonical_path)
        normalized.append({"path": canonical_path, "content": content.rstrip() + "\n"})
        for alias in {
            original_path,
            original_path.replace("\\", "/"),
            Path(original_path).name,
            f"files/{Path(original_path).name}",
            f"evals/files/{Path(original_path).name}",
        }:
            aliases.setdefault(alias, canonical_path)
    return normalized, aliases


def _fallback_generated_cases(
    *,
    skill: Skill,
    selected_flavors: list[str],
    suggested_flavors: list[dict[str, Any]],
    existing_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    titles = {
        str(flavor.get("id") or ""): str(flavor.get("title") or flavor.get("id") or "")
        for flavor in suggested_flavors
    }
    existing_ids = {
        _normalize_slug(str(case.get("id") or f"case-{index}"))
        for index, case in enumerate(existing_payload.get("evals") or [], start=1)
        if isinstance(case, dict)
    }
    generated: list[dict[str, Any]] = []
    used_ids = set(existing_ids)
    for index, flavor_id in enumerate(selected_flavors, start=1):
        case_id = _unique_slug(_normalize_slug(flavor_id or f"generated-{index}"), used_ids)
        used_ids.add(case_id)
        title = titles.get(flavor_id, flavor_id.replace("-", " "))
        generated.append(
            {
                "id": case_id,
                "prompt": f"Handle a realistic request for {skill.name} with emphasis on {title}.",
                "expected_output": "A concise answer that completes the task and stays grounded in the skill's job.",
                "files": [],
                "checks": [
                    {
                        "text": "The answer solves the requested task",
                        "category": "goal",
                        "weight": 3.0,
                    },
                    {
                        "text": "The answer stays narrow and specific",
                        "category": "format",
                        "weight": 1.0,
                    },
                ],
                "required_skill_activations": [],
            }
        )
    return generated


def _materialize_draft(
    *,
    project_root: Path,
    skill: Skill,
    session: dict[str, Any],
    session_dir: Path,
    draft_payload: dict[str, Any],
    existing_payload: dict[str, Any],
) -> dict[str, Any]:
    draft_dir = session_dir / "draft"
    draft_evals_path = write_json(draft_dir / "evals.json", draft_payload["merged_payload"])
    draft_files_root = draft_dir / "files"
    generated_fixture_paths: list[str] = []
    for fixture in draft_payload["generated_fixtures"]:
        relative = Path(str(fixture["path"])).relative_to("evals/files")
        generated_fixture_path = write_text(draft_files_root / relative, str(fixture["content"]))
        generated_fixture_paths.append(_relative_to_project(project_root, generated_fixture_path))

    preview_markdown = draft_payload["preview_markdown"] or _build_preview_markdown(
        skill=skill,
        session=session,
        existing_payload=existing_payload,
        generated_cases=draft_payload["generated_cases"],
        generated_fixtures=draft_payload["generated_fixtures"],
    )
    draft_preview_path = write_text(draft_dir / "preview.md", preview_markdown)
    return {
        "draft_evals_path": _relative_to_project(project_root, draft_evals_path),
        "draft_preview_path": _relative_to_project(project_root, draft_preview_path),
        "draft_fixture_dir": _relative_to_project(project_root, draft_files_root),
        "generated_case_ids": [str(case["id"]) for case in draft_payload["generated_cases"]],
        "generated_fixture_paths": generated_fixture_paths,
    }


def _build_preview_markdown(
    *,
    skill: Skill,
    session: dict[str, Any],
    existing_payload: dict[str, Any],
    generated_cases: list[dict[str, Any]],
    generated_fixtures: list[dict[str, str]],
) -> str:
    lines = [
        f"# Draft Eval Suite For `{skill.name}`",
        "",
        f"- Session: `{session['session_id']}`",
        f"- Selected flavors: {', '.join(session.get('selected_flavors') or []) or 'none'}",
        f"- Preserved existing cases: {len(list(existing_payload.get('evals') or []))}",
        f"- Generated cases: {len(generated_cases)}",
        f"- Generated fixtures: {len(generated_fixtures)}",
        "",
        "## Generated Cases",
    ]
    if generated_cases:
        for case in generated_cases:
            lines.append(f"- `{case['id']}`: {case['prompt']}")
    else:
        lines.append("- none")
    lines.extend(["", "## Generated Fixtures"])
    if generated_fixtures:
        for fixture in generated_fixtures:
            lines.append(f"- `{fixture['path']}`")
    else:
        lines.append("- none")
    return "\n".join(lines) + "\n"


def _build_session_response(
    *,
    project_root: Path,
    skill: Skill,
    session: dict[str, Any],
) -> dict[str, Any]:
    session_dir = _resolve_session_dir(skill, session["session_id"])
    response = {
        "skill_name": skill.name,
        "session_id": session["session_id"],
        "session_dir": _relative_to_project(project_root, session_dir),
        "phase": session.get("phase"),
        "status": session.get("status"),
        "selected_flavors": list(session.get("selected_flavors") or []),
        "author_notes": session.get("author_notes") or "",
        "skill_profile_path": session.get("skill_profile_path"),
        "probe_summary_path": session.get("probe_summary_path"),
        "suggested_flavors_path": session.get("suggested_flavors_path"),
        "draft_evals_path": session.get("draft_evals_path"),
        "draft_preview_path": session.get("draft_preview_path"),
        "draft_fixture_dir": session.get("draft_fixture_dir"),
        "promotion_backup_path": session.get("promotion_backup_path"),
        "promoted_evals_path": session.get("promoted_evals_path"),
        "generated_case_ids": list(session.get("generated_case_ids") or []),
        "generated_fixture_paths": list(session.get("generated_fixture_paths") or []),
        "copied_fixture_paths": list(session.get("copied_fixture_paths") or []),
    }
    if session.get("suggested_flavors_path"):
        suggested_payload = _read_json(project_root / str(session["suggested_flavors_path"]))
        response["suggested_flavors"] = list(suggested_payload.get("suggested_flavors") or [])

    if session.get("phase") == "awaiting_selection":
        response["resume_command"] = (
            f"./molt skill-builder create-evals {skill.name} "
            f"--session {session['session_id']} --answer selected_flavors=<comma-separated ids>"
        )
        response["next_step"] = "Select one or more suggested flavor ids and rerun with --answer."
    elif session.get("phase") == "draft_ready":
        response["promote_command"] = (
            f"./molt skill-builder create-evals {skill.name} "
            f"--session {session['session_id']} --promote"
        )
        response["next_step"] = "Inspect the draft eval suite and promote it when ready."
    elif session.get("phase") == "promoted":
        response["next_command"] = f"./molt skill-builder eval-skill {skill.name}"
        response["next_step"] = "Run the canonical eval suite."
    else:
        response["next_step"] = "Resume the session when you have the next authoring input."
    return response


def _apply_answers(session: dict[str, Any], answers: dict[str, str]) -> None:
    selected_flavors = answers.get("selected_flavors")
    if selected_flavors is not None:
        parsed_flavors = [
            item.strip()
            for item in selected_flavors.split(",")
            if item.strip()
        ]
        session["selected_flavors"] = parsed_flavors
    if "author_notes" in answers:
        session["author_notes"] = answers["author_notes"].strip()


def _create_session_dir(skill: Skill) -> Path:
    workspace_root = skill.path / "evals" / "workspace" / "create-evals"
    workspace_root.mkdir(parents=True, exist_ok=True)
    existing = sorted(
        child
        for child in workspace_root.iterdir()
        if child.is_dir() and re.fullmatch(r"session-\d+", child.name)
    )
    next_index = 1
    if existing:
        next_index = max(int(path.name.split("-")[1]) for path in existing) + 1
    session_dir = workspace_root / f"session-{next_index}"
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def _resolve_session_dir(skill: Skill, session_id: str) -> Path:
    candidate = skill.path / "evals" / "workspace" / "create-evals" / session_id
    if not candidate.is_dir():
        raise ValueError(
            f"Create-evals session '{session_id}' was not found for skill '{skill.name}'."
        )
    return candidate


def _write_session_state(session_dir: Path, session: dict[str, Any]) -> Path:
    return write_json(session_dir / "session.json", session)


def _load_session_state(session_dir: Path) -> dict[str, Any]:
    return _read_json(session_dir / "session.json")


def _load_existing_eval_payload(skill: Skill) -> dict[str, Any]:
    evals_path = skill.path / "evals" / "evals.json"
    if not evals_path.is_file():
        return {"skill_name": skill.name, "evals": []}
    payload = _read_json(evals_path)
    if "skill_name" not in payload:
        payload["skill_name"] = skill.name
    if not isinstance(payload.get("evals"), list):
        payload["evals"] = []
    return payload


def _find_relevant_lessons(*, project_root: Path, skill: Skill) -> list[dict[str, str]]:
    lessons_root = project_root / "lessons"
    if not lessons_root.exists():
        return []
    matches: list[dict[str, str]] = []
    targets = {skill.name.lower(), f"skills/{skill.name}/".lower()}
    for lesson_path in sorted(lessons_root.rglob("*.md")):
        text = lesson_path.read_text(encoding="utf-8")
        lowered = text.lower()
        if not any(target in lowered for target in targets):
            continue
        matches.append(
            {
                "path": _relative_to_project(project_root, lesson_path),
                "excerpt": _truncate_text(text, max_chars=3000),
            }
        )
    return matches[:4]


def _find_latest_iteration_dir(skill: Skill) -> Path | None:
    workspace_root = skill.path / "evals" / "workspace"
    if not workspace_root.exists():
        return None
    iterations = [
        child
        for child in workspace_root.iterdir()
        if child.is_dir() and re.fullmatch(r"iteration-\d+", child.name)
    ]
    if not iterations:
        return None
    return sorted(iterations, key=lambda path: int(path.name.split("-")[1]), reverse=True)[0]


def _read_iteration_artifacts(
    *,
    project_root: Path,
    iteration_dir: Path | None,
    pattern: str,
) -> list[dict[str, str]]:
    if iteration_dir is None:
        return []
    artifacts: list[dict[str, str]] = []
    for artifact_path in sorted(iteration_dir.glob(pattern))[:3]:
        artifacts.append(
            {
                "path": _relative_to_project(project_root, artifact_path),
                "excerpt": _read_text_excerpt(artifact_path),
            }
        )
    return artifacts


def _sanitize_fixture_path(path: str, *, index: int) -> str:
    candidate = Path(path.replace("\\", "/"))
    stem = candidate.stem or f"generated-{index}"
    stem = _normalize_slug(stem)
    extension = candidate.suffix.lower()
    if extension not in ALLOWED_FIXTURE_EXTENSIONS:
        extension = ".md"
    if not stem:
        stem = f"generated-{index}"
    return f"evals/files/{stem}{extension}"


def _ensure_unique_fixture_path(path: str, used_paths: set[str]) -> str:
    if path not in used_paths:
        return path
    candidate = Path(path)
    stem = candidate.stem
    suffix = candidate.suffix
    counter = 2
    while True:
        updated = candidate.with_name(f"{stem}-{counter}{suffix}").as_posix()
        if updated not in used_paths:
            return updated
        counter += 1


def _coerce_suggested_flavor_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, SuggestedFlavorPayload):
        return value.model_dump()
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        if isinstance(dumped, dict):
            return dumped
    payload = _parse_json_payload(value)
    if isinstance(payload, list):
        payload = {"suggested_flavors": payload}
    if not isinstance(payload, dict):
        return {"suggested_flavors": []}
    try:
        return SuggestedFlavorPayload.model_validate(payload).model_dump()
    except Exception:
        return {"suggested_flavors": list(payload.get("suggested_flavors") or [])}


def _coerce_draft_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, DraftSuitePayload):
        return value.model_dump()
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        if isinstance(dumped, dict):
            return dumped
    payload = _parse_json_payload(value)
    if not isinstance(payload, dict):
        return {"evals": [], "fixtures": [], "preview_markdown": ""}
    try:
        return DraftSuitePayload.model_validate(payload).model_dump()
    except Exception:
        payload.setdefault("evals", [])
        payload.setdefault("fixtures", [])
        payload.setdefault("preview_markdown", "")
        return payload


def _parse_json_payload(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        return value
    raw_text = str(value)
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        start = raw_text.find("{")
        end = raw_text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw_text[start : end + 1])
        start = raw_text.find("[")
        end = raw_text.rfind("]")
        if start != -1 and end != -1 and end > start:
            return json.loads(raw_text[start : end + 1])
        raise ValueError("Authoring model did not return valid JSON.")


def _fallback_suggested_flavors(
    *,
    existing_payload: dict[str, Any],
    probe_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    existing_count = len(list(existing_payload.get("evals") or []))
    probe_ids = [str(probe.get("probe_id") or "") for probe in probe_payload.get("probes") or []]
    evidence = [f"Probe evidence from {probe_id}" for probe_id in probe_ids if probe_id]
    if not evidence:
        evidence = ["No probe evidence was available; use additive baseline coverage."]
    return [
        {
            "id": "core-task",
            "title": "Core Task Coverage",
            "rationale": "Cover the most central user task implied by the skill.",
            "recommended": True,
            "evidence": evidence[:2],
            "fixture_strategy": "Reuse an existing local artifact if one already matches the core task.",
        },
        {
            "id": "evidence-discipline",
            "title": "Evidence Discipline",
            "rationale": "Test whether the answer stays grounded in concrete local artifacts or evidence.",
            "recommended": existing_count == 0,
            "evidence": evidence[:2],
            "fixture_strategy": "Add one narrow local fixture when the skill benefits from artifact grounding.",
        },
        {
            "id": "edge-or-variation",
            "title": "Edge Or Variation Case",
            "rationale": "Expand beyond the most obvious prompt with one realistic variation or failure shape.",
            "recommended": False,
            "evidence": evidence[-2:],
            "fixture_strategy": "Use a second fixture only when it reveals a materially different behavior.",
        },
    ]


def _coerce_evidence_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _build_timing_payload(output: dict[str, Any]) -> dict[str, int]:
    metrics = output.get("metrics", {}) or {}
    usage = metrics.get("usage", {}) or {}
    return {
        "duration_ms": int(metrics.get("duration_ms", 0) or 0),
        "total_tokens": int(usage.get("total_tokens", 0) or 0),
        "input_tokens": int(usage.get("input_tokens", 0) or 0),
        "output_tokens": int(usage.get("output_tokens", 0) or 0),
        "requests": int(usage.get("requests", 0) or 0),
    }


def _load_sdk(project_root: Path):
    load_dotenv = runner._load_dotenv(project_root)
    if load_dotenv is not None:
        load_dotenv(project_root / ".env", override=False)
    sdk = runner._import_openai_agents_sdk(project_root)
    sdk.set_tracing_disabled(True)
    return sdk


def _load_eval_author_skill(project_root: Path) -> Skill:
    skills_by_name = discover_skills(project_root / "skills")
    skill = skills_by_name.get("eval-author")
    if skill is None:
        raise ValueError("Missing required internal skill 'eval-author'.")
    return skill


def _normalize_slug(text: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", text.strip().lower()).strip("-")
    return normalized or "item"


def _unique_slug(candidate: str, used: set[str]) -> str:
    if candidate not in used:
        return candidate
    counter = 2
    while True:
        updated = f"{candidate}-{counter}"
        if updated not in used:
            return updated
        counter += 1


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relative_to_project(project_root: Path, path: Path) -> str:
    return str(path.relative_to(project_root))


def _read_text_excerpt(path: Path, max_chars: int = 5000) -> str:
    return _truncate_text(path.read_text(encoding="utf-8"), max_chars=max_chars)


def _truncate_text(text: str, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "\n[truncated]"
