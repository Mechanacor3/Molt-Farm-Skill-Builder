from __future__ import annotations

import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


SKILL_PATH_PATTERN = re.compile(r"\.agents/skills/(?P<skill_name>[^/]+)/SKILL\.md")


def run_codex_trigger_probe(
    project_root: Path,
    *,
    target_skill: str,
    installed_skills: list[str] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    skills_root = project_root / "skills"
    fixture_root = skills_root / target_skill / "evals" / "codex-cli-probe"
    discover_prompt_source = fixture_root / "discover.md"
    trigger_prompt_source = fixture_root / "trigger.md"
    if not discover_prompt_source.is_file() or not trigger_prompt_source.is_file():
        raise FileNotFoundError(
            f"Codex trigger probe fixtures are missing for skill '{target_skill}' under {fixture_root}."
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
    discover_events = _load_jsonl_events(discover_log)
    trigger_events = _load_jsonl_events(trigger_log)
    discover_messages = _extract_agent_messages(discover_events)
    trigger_messages = _extract_agent_messages(trigger_events)
    read_skill_files = _extract_read_skill_files(trigger_events)
    first_trigger_message = trigger_messages[0] if trigger_messages else ""
    summary = {
        "target_skill": target_skill,
        "installed_skills": installed_skills,
        "sandbox_root": str(sandbox_root),
        "discover_log": str(discover_log),
        "trigger_log": str(trigger_log),
        "discover_exit_code": discover_exit_code,
        "trigger_exit_code": trigger_exit_code,
        "discover_completed": _turn_completed(discover_events),
        "trigger_completed": _turn_completed(trigger_events),
        "discover_first_message": discover_messages[0] if discover_messages else "",
        "discover_last_message": discover_messages[-1] if discover_messages else "",
        "trigger_first_message": first_trigger_message,
        "trigger_last_message": trigger_messages[-1] if trigger_messages else "",
        "trigger_usage": _extract_turn_usage(trigger_events),
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


def _load_jsonl_events(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def _extract_agent_messages(events: list[dict[str, Any]]) -> list[str]:
    messages: list[str] = []
    for event in events:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item") or {}
        if item.get("type") == "agent_message":
            messages.append(str(item.get("text") or ""))
    return messages


def _extract_read_skill_files(events: list[dict[str, Any]]) -> list[str]:
    seen: list[str] = []
    for event in events:
        if event.get("type") not in {"item.started", "item.completed"}:
            continue
        item = event.get("item") or {}
        if item.get("type") != "command_execution":
            continue
        command = str(item.get("command") or "")
        match = SKILL_PATH_PATTERN.search(command)
        if match:
            skill_name = match.group("skill_name")
            if skill_name not in seen:
                seen.append(skill_name)
    return seen


def _turn_completed(events: list[dict[str, Any]]) -> bool:
    return any(event.get("type") == "turn.completed" for event in events)


def _extract_turn_usage(events: list[dict[str, Any]]) -> dict[str, int]:
    for event in events:
        if event.get("type") != "turn.completed":
            continue
        usage = event.get("usage") or {}
        return {
            "input_tokens": int(usage.get("input_tokens", 0) or 0),
            "cached_input_tokens": int(usage.get("cached_input_tokens", 0) or 0),
            "output_tokens": int(usage.get("output_tokens", 0) or 0),
        }
    return {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0}


def _message_mentions_skill(message: str, skill_name: str) -> bool:
    if not message:
        return False
    lowered = message.lower()
    target = skill_name.lower()
    return f"`{target}`" in lowered or target in lowered
