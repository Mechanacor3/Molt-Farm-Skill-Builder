from __future__ import annotations

from .models import AgentDefinition, OperationDefinition


def load_operation(operation_name: str) -> OperationDefinition:
    template = _OPERATION_TEMPLATES.get(operation_name)
    if template is None:
        raise FileNotFoundError(f"Skill-builder operation not found: {operation_name}")
    return OperationDefinition(
        name=template.name,
        description=template.description,
        agent=AgentDefinition(
            name=template.agent.name,
            description=template.agent.description,
            model=template.agent.model,
            skills=list(template.agent.skills),
            tools=list(template.agent.tools),
            context_policy=template.agent.context_policy,
            runtime=template.agent.runtime,
        ),
        inputs=dict(template.inputs),
        logging_policy=template.logging_policy,
        execution_policy=template.execution_policy,
    )


def list_operations() -> list[OperationDefinition]:
    return [load_operation(name) for name in sorted(_OPERATION_TEMPLATES)]


_OPERATION_TEMPLATES: dict[str, OperationDefinition] = {
    "manual-docker-smoke-test": OperationDefinition(
        name="manual-docker-smoke-test",
        description="Propose one narrow Docker build-and-run smoke test for a local repo or artifact.",
        agent=AgentDefinition(
            name="docker-smoke-worker",
            description="Minimal local worker for proposing narrow Docker smoke tests.",
            model="gpt-5",
            skills=["docker-smoke-test"],
            context_policy="least_context",
            runtime="openai_agents",
        ),
        inputs={
            "task": "propose a narrow Docker smoke test for the current repository",
            "dockerfile_path": "Dockerfile",
        },
    ),
    "manual-lesson-extraction": OperationDefinition(
        name="manual-lesson-extraction",
        description="Manually review a run or log and extract lessons.",
        agent=AgentDefinition(
            name="lesson-extractor-worker",
            description="Minimal local worker for extracting lessons from logs and runs.",
            model="gpt-5",
            skills=["lesson-extractor"],
            context_policy="least_context",
            runtime="openai_agents",
        ),
        inputs={
            "task": "extract lessons from the provided run or log",
            "source_path": "",
            "comparison_path": "",
        },
    ),
    "manual-system-map-draft": OperationDefinition(
        name="manual-system-map-draft",
        description="Draft a workflow-first Molt system map from selected lesson files.",
        agent=AgentDefinition(
            name="system-map-draft-worker",
            description="Local worker for drafting a workflow-first lesson wiki.",
            model="gpt-5",
            skills=["llm-wiki"],
            context_policy="least_context",
            runtime="stub",
        ),
        inputs={
            "task": "draft a workflow-first system map from the selected lesson files",
            "lesson_paths": "",
            "lesson_glob": "lessons/*.md",
            "workflow_focus": "",
            "date_from": "",
            "date_to": "",
        },
        execution_policy="system_map_draft",
    ),
    "manual-python-build": OperationDefinition(
        name="manual-python-build",
        description="Build or repair a local Python project with narrow, explicit context.",
        agent=AgentDefinition(
            name="python-builder-worker",
            description="Minimal local worker for building or repairing local Python project structure.",
            model="gpt-5",
            skills=["python-build"],
            context_policy="least_context",
            runtime="openai_agents",
        ),
        inputs={
            "task": "bootstrap or repair the local Python project",
            "target": ".",
            "pyproject_path": "pyproject.toml",
        },
    ),
    "manual-run-summary": OperationDefinition(
        name="manual-run-summary",
        description="Manually summarize a completed run record.",
        agent=AgentDefinition(
            name="run-summarizer-worker",
            description="Minimal local worker for summarizing completed runs.",
            model="gpt-5",
            skills=["run-summarizer"],
            context_policy="least_context",
            runtime="openai_agents",
        ),
        inputs={
            "run_id": "",
            "run_record_path": "",
        },
    ),
    "manual-skill-finding": OperationDefinition(
        name="manual-skill-finding",
        description="Choose the best existing skill or identify a missing one for a task.",
        agent=AgentDefinition(
            name="skill-finder-worker",
            description="Minimal local worker for choosing the best skill for a task.",
            model="gpt-5",
            skills=["skill-finder"],
            context_policy="least_context",
            runtime="openai_agents",
        ),
        inputs={
            "task": "",
            "skill_inventory": "",
        },
    ),
    "manual-skill-refinement": OperationDefinition(
        name="manual-skill-refinement",
        description="Manually refine an existing skill from a narrow brief and supporting lessons.",
        agent=AgentDefinition(
            name="skill-refiner-worker",
            description="Minimal local worker for refining existing skills from lessons and logs.",
            model="gpt-5",
            skills=["skill-refiner"],
            context_policy="least_context",
            runtime="openai_agents",
        ),
        inputs={
            "target_skill": "repo-triage",
            "refinement_brief": "tighten instructions using the latest lesson",
            "lesson_path": "",
            "grading_path": "",
            "feedback_path": "",
            "benchmark_path": "",
            "comparison_path": "",
            "trace_path": "",
        },
    ),
    "manual-triage": OperationDefinition(
        name="manual-triage",
        description="Manually run a narrow repository triage task.",
        agent=AgentDefinition(
            name="triage-worker",
            description="Minimal local worker for repository triage tasks.",
            model="gpt-5",
            skills=["repo-triage"],
            context_policy="least_context",
            runtime="openai_agents",
        ),
        inputs={
            "task": "inspect the repository state",
            "target": ".",
        },
    ),
}
