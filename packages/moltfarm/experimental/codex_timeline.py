from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Iterable

from ..skill_loader import discover_skills
from ..storage import write_json

ANALYSIS_VERSION = 1
DETECTED_FORMAT = "codex_jsonl"
SOURCE_VARIANT_EXEC = "exec"
SOURCE_VARIANT_ARCHIVED_SESSION = "archived_session"
CLAIM_CONFIDENCE = "medium"
INVOCATION_CONFIDENCE = "high"
CLAIM_VERB_PATTERN = re.compile(
    r"\b(using|use|used|activat(?:e|ing|ed)|open(?:ing|ed))\b",
    re.IGNORECASE,
)
SKILL_ARTIFACT_PATTERN = re.compile(
    r"(?P<path>[^\"'`\s;|&()<>]*(?:\.agents|\.codex)/skills/[^\"'`\s;|&()<>]+)"
)


def analyze_codex_jsonl(
    source_path: Path,
    *,
    skill_names: Iterable[str],
) -> dict[str, Any]:
    resolved_source = source_path.resolve()
    raw_events = load_codex_jsonl_events(resolved_source)
    source_variant, normalized_events = normalize_codex_jsonl_events(raw_events)
    known_skill_names = {str(skill_name) for skill_name in skill_names}
    completed_command_item_ids = _completed_command_item_ids(normalized_events)

    timeline_events: list[dict[str, Any]] = []
    usage_by_turn: list[dict[str, int]] = []
    turn_index = 0
    completed_turns = 0

    for raw_event in normalized_events:
        event_type = str(raw_event.get("type") or "")
        if event_type == "turn.started":
            turn_index += 1
            continue
        if event_type == "turn.completed":
            completed_turns += 1
            usage_by_turn.append(
                {
                    "turn_index": turn_index,
                    **extract_turn_usage(raw_event),
                }
            )
            continue

        if event_type not in {"item.started", "item.completed"}:
            continue

        item = raw_event.get("item") or {}
        item_type = str(item.get("type") or "")
        item_id = str(item.get("id") or "") or None

        if item_type == "agent_message" and event_type == "item.completed":
            message = str(item.get("text") or "")
            for skill_name in _extract_claimed_skills(message, known_skill_names):
                timeline_events.append(
                    {
                        "turn_index": turn_index,
                        "item_id": item_id,
                        "event_type": "agent_skill_claim",
                        "skill_name": skill_name,
                        "counts_as_invocation": False,
                        "confidence": CLAIM_CONFIDENCE,
                        "evidence": {
                            "source_event_type": event_type,
                            "message": message,
                        },
                    }
                )
            continue

        if item_type != "command_execution":
            continue

        if event_type == "item.started" and item_id in completed_command_item_ids:
            continue

        command = str(item.get("command") or "")
        for skill_event in _extract_skill_events_from_command(
            command,
            known_skill_names=known_skill_names,
            turn_index=turn_index,
            item_id=item_id,
            source_event_type=event_type,
        ):
            timeline_events.append(skill_event)

    if source_variant == SOURCE_VARIANT_ARCHIVED_SESSION and completed_turns == 0:
        completed_turns = turn_index

    indexed_events = _index_events(timeline_events)
    invocation_events = [event for event in indexed_events if event["counts_as_invocation"]]
    observed_invocation_order = [event["skill_name"] for event in invocation_events]
    first_seen_skill_order = _first_seen_skill_order(invocation_events)
    skills = _build_skill_rollup(indexed_events)
    return {
        "source_path": str(resolved_source),
        "detected_format": DETECTED_FORMAT,
        "source_variant": source_variant,
        "analysis_version": ANALYSIS_VERSION,
        "completed_turns": completed_turns,
        "usage_by_turn": usage_by_turn,
        "events": indexed_events,
        "observed_invocation_order": observed_invocation_order,
        "first_seen_skill_order": first_seen_skill_order,
        "skills": skills,
    }


def write_codex_skill_timeline(
    source_path: Path,
    *,
    skill_names: Iterable[str],
    output_path: Path | None = None,
) -> dict[str, Any]:
    resolved_source = source_path.resolve()
    resolved_output = (
        output_path.resolve()
        if output_path is not None
        else resolved_source.with_name(f"{resolved_source.stem}.skill-trace.json")
    )
    payload = analyze_codex_jsonl(resolved_source, skill_names=skill_names)
    write_json(resolved_output, payload)
    return {
        **payload,
        "output_path": str(resolved_output),
    }


def discover_analysis_skill_names(
    *,
    project_root: Path | None = None,
    codex_home: Path | None = None,
) -> list[str]:
    skill_names: set[str] = set()
    if project_root is not None:
        skill_names.update(discover_skills(project_root / "skills"))

    codex_root = resolve_codex_home(codex_home) / "skills"
    skill_names.update(discover_skills(codex_root))
    return sorted(skill_names)


def resolve_codex_home(codex_home: Path | None = None) -> Path:
    if codex_home is not None:
        return codex_home.resolve()

    configured_home = os.environ.get("CODEX_HOME")
    if configured_home:
        return Path(configured_home).expanduser().resolve()
    return (Path.home() / ".codex").resolve()


def load_codex_jsonl_events(path: Path) -> list[dict[str, Any]]:
    resolved_path = path.resolve()
    if not resolved_path.is_file():
        raise FileNotFoundError(f"Codex JSONL log not found: {resolved_path}")
    events: list[dict[str, Any]] = []
    for line in resolved_path.read_text(encoding="utf-8").splitlines():
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


def normalize_codex_jsonl_events(events: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    source_variant = detect_codex_jsonl_source_variant(events)
    if source_variant == SOURCE_VARIANT_ARCHIVED_SESSION:
        return source_variant, _normalize_archived_session_events(events)
    return SOURCE_VARIANT_EXEC, events


def detect_codex_jsonl_source_variant(events: list[dict[str, Any]]) -> str:
    for event in events:
        event_type = str(event.get("type") or "")
        if event_type in {"response_item", "event_msg", "turn_context", "session_meta"}:
            return SOURCE_VARIANT_ARCHIVED_SESSION
        if event_type in {"thread.started", "turn.started", "turn.completed", "item.started", "item.completed"}:
            return SOURCE_VARIANT_EXEC
    return SOURCE_VARIANT_EXEC


def extract_agent_messages(events: list[dict[str, Any]]) -> list[str]:
    messages: list[str] = []
    for event in events:
        event_type = str(event.get("type") or "")
        if event_type == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message":
                messages.append(str(item.get("text") or ""))
            continue
        if event_type != "event_msg":
            continue
        payload = event.get("payload") or {}
        if payload.get("type") == "agent_message":
            messages.append(str(payload.get("message") or ""))
    return messages


def count_completed_turns(events: list[dict[str, Any]]) -> int:
    return sum(1 for event in events if event.get("type") == "turn.completed")


def extract_turn_usage(event: dict[str, Any]) -> dict[str, int]:
    usage = event.get("usage") or {}
    return {
        "input_tokens": int(usage.get("input_tokens", 0) or 0),
        "cached_input_tokens": int(usage.get("cached_input_tokens", 0) or 0),
        "output_tokens": int(usage.get("output_tokens", 0) or 0),
    }


def _normalize_archived_session_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized_events: list[dict[str, Any]] = []
    for event in events:
        event_type = str(event.get("type") or "")
        payload = event.get("payload") or {}
        if event_type == "turn_context":
            normalized_events.append({"type": "turn.started"})
            continue

        if event_type == "event_msg" and payload.get("type") == "agent_message":
            normalized_events.append(
                {
                    "type": "item.completed",
                    "item": {
                        "id": str(event.get("timestamp") or "") or None,
                        "type": "agent_message",
                        "text": str(payload.get("message") or ""),
                    },
                }
            )
            continue

        if event_type != "response_item" or payload.get("type") != "function_call":
            continue

        call_id = str(payload.get("call_id") or event.get("timestamp") or "")
        for index, command in enumerate(_extract_archived_commands(payload), start=1):
            normalized_events.append(
                {
                    "type": "item.completed",
                    "item": {
                        "id": f"{call_id}:{index}" if call_id else None,
                        "type": "command_execution",
                        "command": command,
                    },
                }
            )
    return normalized_events


def _extract_archived_commands(payload: dict[str, Any]) -> list[str]:
    function_name = str(payload.get("name") or "")
    arguments = _parse_json_object(payload.get("arguments"))
    if function_name in {"exec_command", "functions.exec_command"}:
        command = arguments.get("cmd")
        if isinstance(command, str) and command:
            return [command]
        return []

    if function_name in {"parallel", "multi_tool_use.parallel"}:
        commands: list[str] = []
        for tool_use in arguments.get("tool_uses") or []:
            if not isinstance(tool_use, dict):
                continue
            if str(tool_use.get("recipient_name") or "") != "functions.exec_command":
                continue
            parameters = tool_use.get("parameters") or {}
            if not isinstance(parameters, dict):
                continue
            command = parameters.get("cmd")
            if isinstance(command, str) and command:
                commands.append(command)
        return commands

    return []


def _parse_json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return {}
    if isinstance(parsed, dict):
        return parsed
    return {}


def _completed_command_item_ids(events: list[dict[str, Any]]) -> set[str]:
    completed_ids: set[str] = set()
    for event in events:
        if event.get("type") != "item.completed":
            continue
        item = event.get("item") or {}
        if item.get("type") != "command_execution":
            continue
        item_id = str(item.get("id") or "")
        if item_id:
            completed_ids.add(item_id)
    return completed_ids


def _extract_claimed_skills(message: str, known_skill_names: set[str]) -> list[str]:
    if not message or not known_skill_names or not CLAIM_VERB_PATTERN.search(message):
        return []

    lowered_message = message.lower()
    claimed_skills: list[str] = []
    for skill_name in sorted(known_skill_names):
        lowered_skill = skill_name.lower()
        if f"`{lowered_skill}`" in lowered_message or lowered_skill in lowered_message:
            claimed_skills.append(skill_name)
    return claimed_skills


def _extract_skill_events_from_command(
    command: str,
    *,
    known_skill_names: set[str],
    turn_index: int,
    item_id: str | None,
    source_event_type: str,
) -> list[dict[str, Any]]:
    seen_paths: set[tuple[str, str]] = set()
    extracted_events: list[dict[str, Any]] = []
    for match in SKILL_ARTIFACT_PATTERN.finditer(command):
        full_path = str(match.group("path") or "")
        resolved = _resolve_skill_artifact(full_path, known_skill_names)
        if resolved is None:
            continue
        skill_name, relative_path = resolved
        dedupe_key = (skill_name, relative_path)
        if dedupe_key in seen_paths:
            continue
        seen_paths.add(dedupe_key)
        event_type = "skill_file_read" if relative_path == "SKILL.md" else "skill_resource_read"
        extracted_events.append(
            {
                "turn_index": turn_index,
                "item_id": item_id,
                "event_type": event_type,
                "skill_name": skill_name,
                "counts_as_invocation": True,
                "confidence": INVOCATION_CONFIDENCE,
                "evidence": {
                    "source_event_type": source_event_type,
                    "command": command,
                    "path": full_path,
                    "relative_skill_path": relative_path,
                },
            }
        )
    return extracted_events


def _resolve_skill_artifact(full_path: str, known_skill_names: set[str]) -> tuple[str, str] | None:
    skill_path = _extract_path_within_skills_root(full_path)
    if skill_path is None:
        return None

    parts = [part for part in skill_path.split("/") if part]
    if len(parts) < 2:
        return None

    for index in range(1, len(parts)):
        candidate_name = parts[index - 1]
        if candidate_name in known_skill_names:
            return candidate_name, "/".join(parts[index:])

    fallback_index = 0
    while fallback_index < len(parts) - 1 and parts[fallback_index].startswith("."):
        fallback_index += 1
    if fallback_index >= len(parts) - 1:
        return None
    return parts[fallback_index], "/".join(parts[fallback_index + 1 :])


def _extract_path_within_skills_root(full_path: str) -> str | None:
    for marker in (".agents/skills/", ".codex/skills/"):
        marker_index = full_path.find(marker)
        if marker_index >= 0:
            return full_path[marker_index + len(marker) :]
    return None


def _index_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    indexed_events: list[dict[str, Any]] = []
    for index, event in enumerate(events, start=1):
        indexed_events.append(
            {
                "index": index,
                **event,
            }
        )
    return indexed_events


def _first_seen_skill_order(events: list[dict[str, Any]]) -> list[str]:
    ordered: list[str] = []
    for event in events:
        skill_name = str(event["skill_name"])
        if skill_name not in ordered:
            ordered.append(skill_name)
    return ordered


def _build_skill_rollup(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    skills: dict[str, dict[str, Any]] = {}
    for event in events:
        skill_name = str(event["skill_name"])
        event_index = int(event["index"])
        if skill_name not in skills:
            skills[skill_name] = {
                "first_seen_index": event_index,
                "first_invocation_index": None,
                "event_count": 0,
                "invocation_event_count": 0,
                "has_invocation": False,
            }
        skills[skill_name]["event_count"] += 1
        if event["counts_as_invocation"]:
            skills[skill_name]["invocation_event_count"] += 1
            skills[skill_name]["has_invocation"] = True
            if skills[skill_name]["first_invocation_index"] is None:
                skills[skill_name]["first_invocation_index"] = event_index
    return skills
