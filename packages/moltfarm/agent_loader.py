from __future__ import annotations

from pathlib import Path

import yaml

from .models import AgentDefinition


def load_agent(agent_root: Path, agent_name: str) -> AgentDefinition:
    agent_file = agent_root / agent_name / "agent.yaml"
    if not agent_file.exists():
        raise FileNotFoundError(f"Agent definition not found: {agent_file}")

    data = yaml.safe_load(agent_file.read_text(encoding="utf-8")) or {}
    return AgentDefinition(
        name=data.get("name", agent_name),
        description=data.get("description", ""),
        model=data.get("model", "stub-model"),
        skills=list(data.get("skills", [])),
        tools=list(data.get("tools", [])),
        context_policy=data.get("context_policy", "least_context"),
        runtime=data.get("runtime", "stub"),
        path=agent_file,
    )
