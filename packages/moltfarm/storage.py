from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .models import RunResult


def generate_run_id(now: datetime | None = None) -> str:
    current = now or datetime.now()
    return f"run-{current.strftime('%Y%m%d%H%M%S')}-{uuid4().hex[:8]}"


def write_run_record(project_root: Path, payload: dict) -> Path:
    runs_dir = project_root / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_path = runs_dir / f"{payload['run_id']}.json"
    run_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return run_path


def write_json(path: Path, payload: dict | list) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_log(
    project_root: Path,
    *,
    run_id: str,
    agent_name: str,
    skill_names: list[str],
    summary: str,
) -> Path:
    dated_dir = project_root / "logs" / datetime.now().strftime("%Y-%m-%d")
    dated_dir.mkdir(parents=True, exist_ok=True)
    log_path = dated_dir / f"{run_id}.log"
    lines = [
        f"run_id: {run_id}",
        f"agent: {agent_name}",
        f"skills: {', '.join(skill_names) if skill_names else 'none'}",
        f"summary: {summary}",
    ]
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return log_path


def result_to_payload(result: RunResult) -> dict:
    return asdict(result)
