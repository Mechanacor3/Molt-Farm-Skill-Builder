from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .codex_timeline import (
    analyze_codex_jsonl,
    count_completed_turns,
    extract_agent_messages,
    extract_turn_usage,
    load_codex_jsonl_events,
)


def run_codex_trigger_probe(
    project_root: Path,
    *,
    target_skill: str,
    installed_skills: list[str] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    skills_root = project_root / "skills"
    fixture_root = project_root / "experiments" / "codex-trigger-probe" / target_skill
    discover_prompt_source = fixture_root / "discover.md"
    trigger_prompt_source = fixture_root / "trigger.md"
    if not discover_prompt_source.is_file() or not trigger_prompt_source.is_file():
        raise FileNotFoundError(
            f"Experimental Codex probe fixtures are missing for skill '{target_skill}' under {fixture_root}."
        )

    installed = _normalize_installed_skills(target_skill, installed_skills)
    sandbox_root = _create_probe_workspace(project_root, target_skill)
    _install_skills(skills_root=skills_root, sandbox_root=sandbox_root, skill_names=installed)
    _copy_probe_prompts(
        sandbox_root=sandbox_root,
        discover_prompt_source=discover_prompt_source,
        trigger_prompt_source=trigger_prompt_source,
    )
    _init_probe_git_repo(sandbox_root)

    discover_log = sandbox_root / "discover.jsonl"
    trigger_log = sandbox_root / "trigger.jsonl"
    discover_exit = _run_codex_exec(
        sandbox_root=sandbox_root,
        prompt_path=sandbox_root / "DISCOVER.md",
        output_path=discover_log,
        model=model,
    )
    trigger_exit = _run_codex_exec(
        sandbox_root=sandbox_root,
        prompt_path=sandbox_root / "TRIGGER.md",
        output_path=trigger_log,
        model=model,
    )

    summary = summarize_codex_trigger_probe(
        sandbox_root=sandbox_root,
        target_skill=target_skill,
        installed_skills=installed,
        discover_log=discover_log,
        trigger_log=trigger_log,
        discover_exit_code=discover_exit,
        trigger_exit_code=trigger_exit,
    )
    summary_path = sandbox_root / "probe-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["summary_path"] = str(summary_path.relative_to(project_root))
    return summary


def summarize_codex_trigger_probe(
    *,
    sandbox_root: Path,
    target_skill: str,
    installed_skills: list[str],
    discover_log: Path,
    trigger_log: Path,
    discover_exit_code: int,
    trigger_exit_code: int,
) -> dict[str, Any]:
    discover_events = load_codex_jsonl_events(discover_log)
    trigger_events = load_codex_jsonl_events(trigger_log)
    discover_messages = extract_agent_messages(discover_events)
    trigger_messages = extract_agent_messages(trigger_events)
    trigger_timeline = analyze_codex_jsonl(trigger_log, skill_names=installed_skills)
    read_skill_files = _unique_skill_file_reads(trigger_timeline)
    first_trigger_message = trigger_messages[0] if trigger_messages else ""
    summary = {
        "target_skill": target_skill,
        "installed_skills": installed_skills,
        "sandbox_root": str(sandbox_root),
        "discover_log": str(discover_log),
        "trigger_log": str(trigger_log),
        "discover_exit_code": discover_exit_code,
        "trigger_exit_code": trigger_exit_code,
        "discover_completed": count_completed_turns(discover_events) > 0,
        "trigger_completed": count_completed_turns(trigger_events) > 0,
        "discover_first_message": discover_messages[0] if discover_messages else "",
        "discover_last_message": discover_messages[-1] if discover_messages else "",
        "trigger_first_message": first_trigger_message,
        "trigger_last_message": trigger_messages[-1] if trigger_messages else "",
        "trigger_usage": _last_turn_usage(trigger_events),
        "read_skill_files": read_skill_files,
        "first_message_mentions_target": _message_mentions_skill(first_trigger_message, target_skill),
        "first_read_skill": read_skill_files[0] if read_skill_files else None,
        "first_read_is_target": bool(read_skill_files and read_skill_files[0] == target_skill),
    }
    summary["target_triggered_first"] = bool(
        summary["first_message_mentions_target"] or summary["first_read_is_target"]
    )
    return summary


def _normalize_installed_skills(target_skill: str, installed_skills: list[str] | None) -> list[str]:
    ordered = [target_skill]
    for skill_name in installed_skills or []:
        if skill_name not in ordered:
            ordered.append(skill_name)
    return ordered


def _create_probe_workspace(project_root: Path, target_skill: str) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    sandbox_root = project_root / "tmp" / "codex-trigger-probes" / (
        f"{target_skill}-{timestamp}-{uuid4().hex[:8]}"
    )
    (sandbox_root / ".agents" / "skills").mkdir(parents=True, exist_ok=True)
    return sandbox_root


def _install_skills(*, skills_root: Path, sandbox_root: Path, skill_names: list[str]) -> None:
    destination_root = sandbox_root / ".agents" / "skills"
    for skill_name in skill_names:
        source_dir = skills_root / skill_name
        if not source_dir.is_dir():
            raise FileNotFoundError(f"Skill directory not found for probe install: {source_dir}")
        shutil.copytree(source_dir, destination_root / skill_name)


def _copy_probe_prompts(
    *,
    sandbox_root: Path,
    discover_prompt_source: Path,
    trigger_prompt_source: Path,
) -> None:
    shutil.copyfile(discover_prompt_source, sandbox_root / "DISCOVER.md")
    shutil.copyfile(trigger_prompt_source, sandbox_root / "TRIGGER.md")


def _init_probe_git_repo(sandbox_root: Path) -> None:
    subprocess.run(
        ["git", "-C", str(sandbox_root), "init", "-q"],
        check=True,
        capture_output=True,
        text=True,
    )


def _run_codex_exec(
    *,
    sandbox_root: Path,
    prompt_path: Path,
    output_path: Path,
    model: str | None,
) -> int:
    command = [
        "codex",
        "exec",
        "--json",
        "--ephemeral",
        "-C",
        str(sandbox_root),
        "-s",
        "read-only",
    ]
    if model:
        command.extend(["-m", model])
    command.append("-")
    with prompt_path.open("rb") as prompt_file, output_path.open("wb") as output_file:
        result = subprocess.run(
            command,
            stdin=prompt_file,
            stdout=output_file,
            stderr=subprocess.STDOUT,
            check=False,
        )
    return int(result.returncode)


def _last_turn_usage(events: list[dict[str, Any]]) -> dict[str, int]:
    for event in events:
        if event.get("type") != "turn.completed":
            continue
        return extract_turn_usage(event)
    return {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}


def _unique_skill_file_reads(timeline: dict[str, Any]) -> list[str]:
    seen: list[str] = []
    for event in timeline.get("events", []):
        if event.get("event_type") != "skill_file_read":
            continue
        skill_name = str(event.get("skill_name") or "")
        if skill_name and skill_name not in seen:
            seen.append(skill_name)
    return seen


def _message_mentions_skill(message: str, skill_name: str) -> bool:
    if not message:
        return False
    lowered = message.lower()
    target = skill_name.lower()
    return f"`{target}`" in lowered or target in lowered
