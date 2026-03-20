from __future__ import annotations

from pathlib import Path

import yaml

from .models import WorkflowDefinition


def load_workflow(workflow_root: Path, workflow_name: str) -> WorkflowDefinition:
    workflow_file = workflow_root / workflow_name / "molt.yaml"
    if not workflow_file.exists():
        raise FileNotFoundError(f"Workflow definition not found: {workflow_file}")

    data = yaml.safe_load(workflow_file.read_text(encoding="utf-8")) or {}
    return WorkflowDefinition(
        name=data.get("name", workflow_name),
        description=data.get("description", ""),
        entry_agent=data.get("entry_agent", ""),
        inputs=dict(data.get("inputs", {})),
        logging_policy=data.get("logging_policy", "per_run"),
        execution_policy=data.get("execution_policy", "local"),
        path=workflow_file,
    )
