from __future__ import annotations

import importlib
import math
import sys
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Any

from .agent_loader import load_agent
from .models import AgentDefinition, RunResult, Skill
from .skill_loader import discover_skills
from .storage import generate_run_id, result_to_payload, write_log, write_run_record
from .workflow_loader import load_workflow

COMPACTION_TOKEN_THRESHOLD = 100_000
COMPACTION_TARGET_TOKENS = 20_000
COMPACTION_SOURCE_MAX_TOKENS = 120_000


class StubAgentExecutor:
    """
    Minimal executor for the first milestone.

    The interface is shaped so a real Agents SDK-backed implementation can
    replace this later without changing the CLI or storage layers.
    """

    def run(
        self,
        *,
        project_root: Path,
        agent: AgentDefinition,
        skills: list[Skill],
        task_input: dict[str, Any],
    ) -> dict[str, Any]:
        context_files = _collect_context_files(project_root, task_input)
        context_directories = _collect_context_directories(project_root, task_input)
        summary = self._build_summary(agent=agent, skills=skills, task_input=task_input)
        return {
            "summary": summary,
            "skill_names": [skill.name for skill in skills],
            "skill_descriptions": {
                skill.name: skill.description for skill in skills
            },
            "skill_references": {
                skill.name: [path.as_posix() for path in skill.referenced_paths]
                for skill in skills
            },
            "skill_catalog": _build_skill_catalog(skills),
            "context_files": context_files,
            "context_directories": context_directories,
            "runtime": agent.runtime,
            "model": agent.model,
            "task_input": task_input,
            "compaction": {
                "threshold_tokens": COMPACTION_TOKEN_THRESHOLD,
                "input_tokens_estimate": 0,
                "input_compacted": False,
                "output_tokens_estimate": 0,
                "output_compacted": False,
            },
        }

    def _build_summary(
        self,
        *,
        agent: AgentDefinition,
        skills: list[Skill],
        task_input: dict[str, Any],
    ) -> str:
        skill_names = ", ".join(skill.name for skill in skills) or "no skills"
        input_keys = ", ".join(sorted(task_input)) or "no inputs"
        task_label = task_input.get("task") or task_input.get("target") or "execute the workflow task"
        return (
            f"{agent.name} would use {skill_names} to {task_label}. "
            f"Observed input keys: {input_keys}. "
            f"Runtime={agent.runtime}, context_policy={agent.context_policy}."
        )


class OpenAIAgentsExecutor:
    """Execute a workflow with the OpenAI Agents SDK."""

    def run(
        self,
        *,
        project_root: Path,
        agent: AgentDefinition,
        skills: list[Skill],
        task_input: dict[str, Any],
    ) -> dict[str, Any]:
        load_dotenv = _load_dotenv(project_root)
        if load_dotenv is not None:
            # Load API keys from .env without inspecting or printing its contents.
            load_dotenv(project_root / ".env", override=False)

        sdk = _import_openai_agents_sdk(project_root)
        sdk.set_tracing_disabled(True)
        context_files = _collect_context_files(project_root, task_input)
        context_directories = _collect_context_directories(project_root, task_input)
        activation_tool = _build_activate_skill_tool(sdk=sdk, skills=skills)
        resource_tool = _build_read_skill_resource_tool(sdk=sdk, skills=skills)
        raw_input = _build_sdk_input(
            project_root=project_root,
            task_input=task_input,
            context_files=context_files,
            context_directories=context_directories,
        )
        model_input, compaction = _maybe_compact_input(
            sdk=sdk,
            model=agent.model,
            input_text=raw_input,
        )
        sdk_agent = sdk.Agent(
            name=agent.name,
            model=agent.model,
            instructions=_build_sdk_instructions(agent=agent, skills=skills),
            tools=[activation_tool, resource_tool],
        )
        result = sdk.Runner.run_sync(
            sdk_agent,
            model_input,
        )
        final_output = _coerce_final_output(result.final_output)
        final_output, compaction = _maybe_compact_output(
            sdk=sdk,
            model=agent.model,
            output_text=final_output,
            compaction=compaction,
        )
        return {
            "summary": final_output,
            "skill_names": [skill.name for skill in skills],
            "skill_descriptions": {
                skill.name: skill.description for skill in skills
            },
            "skill_references": {
                skill.name: [path.as_posix() for path in skill.referenced_paths]
                for skill in skills
            },
            "skill_catalog": _build_skill_catalog(skills),
            "context_files": context_files,
            "context_directories": context_directories,
            "runtime": agent.runtime,
            "model": agent.model,
            "task_input": task_input,
            "compaction": compaction,
        }


def run_workflow(
    project_root: Path,
    workflow_name: str,
    overrides: dict[str, Any] | None = None,
) -> RunResult:
    workflow = load_workflow(project_root / "workflows", workflow_name)
    agent = load_agent(project_root / "agents", workflow.entry_agent)
    skills_by_name = discover_skills(project_root / "skills")
    attached_skills = _resolve_skills(agent, skills_by_name)

    task_input = dict(workflow.inputs)
    if overrides:
        task_input.update(overrides)
    _augment_task_input_with_local_skill_paths(
        task_input=task_input,
        project_root=project_root,
        skills_by_name=skills_by_name,
    )

    executor = _build_executor(agent.runtime)
    run_id = generate_run_id()
    status = "completed"
    try:
        output = executor.run(
            project_root=project_root,
            agent=agent,
            skills=attached_skills,
            task_input=task_input,
        )
    except Exception as exc:
        status = "failed"
        output = _build_failed_output(
            agent=agent,
            skills=attached_skills,
            task_input=task_input,
            error=exc,
        )

    log_path = write_log(
        project_root,
        run_id=run_id,
        agent_name=agent.name,
        skill_names=output["skill_names"],
        summary=output["summary"],
    )

    result = RunResult(
        run_id=run_id,
        workflow=workflow.name,
        agent=agent.name,
        status=status,
        inputs=task_input,
        output=output,
        log_path=str(log_path.relative_to(project_root)),
        run_path="",
    )
    result.run_path = f"runs/{run_id}.json"
    write_run_record(project_root, result_to_payload(result))
    return result


def _build_executor(runtime: str) -> StubAgentExecutor | OpenAIAgentsExecutor:
    if runtime == "openai_agents":
        return OpenAIAgentsExecutor()
    return StubAgentExecutor()


def _resolve_skills(
    agent: AgentDefinition,
    skills_by_name: dict[str, Skill],
) -> list[Skill]:
    resolved: list[Skill] = []
    for skill_name in agent.skills:
        skill = skills_by_name.get(skill_name)
        if skill is None:
            raise ValueError(
                f"Agent '{agent.name}' references missing skill '{skill_name}'."
            )
        resolved.append(skill)
    return resolved


def _augment_task_input_with_local_skill_paths(
    *,
    task_input: dict[str, Any],
    project_root: Path,
    skills_by_name: dict[str, Skill],
) -> None:
    target_skill = task_input.get("target_skill")
    if not isinstance(target_skill, str) or not target_skill:
        return
    skill = skills_by_name.get(target_skill)
    if skill is None:
        return
    skill_file = skill.path / "SKILL.md"
    task_input.setdefault(
        "target_skill_path",
        str(skill_file.relative_to(project_root)),
    )


def _build_sdk_instructions(agent: AgentDefinition, skills: list[Skill]) -> str:
    skill_catalog = _build_skill_catalog(skills)
    catalog_lines = ["<available_skills>"]
    for entry in skill_catalog:
        catalog_lines.extend(
            [
                "  <skill>",
                f"    <name>{entry['name']}</name>",
                f"    <description>{entry['description']}</description>",
                "  </skill>",
            ]
        )
    catalog_lines.append("</available_skills>")

    parts = [
        f"You are {agent.name}.",
        f"Context policy: {agent.context_policy}.",
        "You have access to specialized skills.",
        "Start from the skill catalog only. Do not assume full skill instructions are already loaded.",
        "When a task matches a skill's description, call the activate_skill tool with the matching skill name to load its wrapped instructions before proceeding.",
        "When the activated skill lists bundled resources, call read_skill_resource only for the specific files you need.",
        "Explicit workflow input files and directory snapshots may already be included below; use those before asking for more context.",
        "\n".join(catalog_lines),
    ]
    return "\n\n".join(parts)


def _build_sdk_input(
    *,
    project_root: Path,
    task_input: dict[str, Any],
    context_files: list[str],
    context_directories: list[str],
) -> str:
    lines = ["Workflow input:"]
    for key in sorted(task_input):
        lines.append(f"- {key}: {task_input[key]}")
    if context_files:
        lines.append("")
        lines.append("Explicit workflow context files:")
        for relative_path in context_files:
            lines.extend(
                [
                    f"<context_file path=\"{relative_path}\">",
                    _read_text_for_prompt(project_root / relative_path),
                    "</context_file>",
                ]
            )
    if context_directories:
        lines.append("")
        lines.append("Explicit workflow directory snapshots:")
        for relative_path in context_directories:
            lines.extend(
                [
                    f"<context_directory path=\"{relative_path}\">",
                    _list_directory_for_prompt(project_root / relative_path),
                    "</context_directory>",
                ]
            )
    return "\n".join(lines)


def _build_skill_catalog(skills: list[Skill]) -> list[dict[str, str]]:
    return [
        {
            "name": skill.name,
            "description": skill.description,
        }
        for skill in skills
    ]


def _build_failed_output(
    *,
    agent: AgentDefinition,
    skills: list[Skill],
    task_input: dict[str, Any],
    error: Exception,
) -> dict[str, Any]:
    return {
        "summary": f"Run failed: {type(error).__name__}: {error}",
        "skill_names": [skill.name for skill in skills],
        "skill_descriptions": {
            skill.name: skill.description for skill in skills
        },
        "skill_references": {
            skill.name: [path.as_posix() for path in skill.referenced_paths]
            for skill in skills
        },
        "skill_catalog": _build_skill_catalog(skills),
        "context_files": [],
        "context_directories": [],
        "runtime": agent.runtime,
        "model": agent.model,
        "task_input": task_input,
        "compaction": {
            "threshold_tokens": COMPACTION_TOKEN_THRESHOLD,
            "input_tokens_estimate": 0,
            "input_compacted": False,
            "output_tokens_estimate": 0,
            "output_compacted": False,
        },
        "error": {
            "type": type(error).__name__,
            "message": str(error),
        },
    }


def _build_activate_skill_tool(sdk: Any, skills: list[Skill]):
    if not skills:
        raise ValueError("activate_skill tool requires at least one skill.")

    skill_map = {skill.name: skill for skill in skills}
    enum_members = {
        _sanitize_enum_member_name(skill_name): skill_name
        for skill_name in skill_map
    }
    skill_name_enum = Enum("SkillName", enum_members, type=str)

    def activate_skill(name) -> str:
        """Load one skill's instructions and bundled resource map by exact name."""
        skill_name = name.value if isinstance(name, Enum) else str(name)
        skill = skill_map[skill_name]
        return _wrap_skill_activation(skill)

    activate_skill.__annotations__ = {
        "name": skill_name_enum,
        "return": str,
    }
    return sdk.function_tool(activate_skill)


def _build_read_skill_resource_tool(sdk: Any, skills: list[Skill]):
    skill_map = {skill.name: skill for skill in skills}
    enum_members = {
        _sanitize_enum_member_name(skill_name): skill_name
        for skill_name in skill_map
    }
    skill_name_enum = Enum("SkillResourceName", enum_members, type=str)

    def read_skill_resource(name, path: str) -> str:
        """Read one bundled resource from an activated skill by exact skill name and relative path."""
        skill_name = name.value if isinstance(name, Enum) else str(name)
        skill = skill_map[skill_name]
        relative_path = Path(path)
        allowed_paths = {
            resource_path
            for _, resources in skill.resources.iter_categories()
            for resource_path in resources
        }
        if relative_path not in allowed_paths:
            raise ValueError(
                f"Resource '{path}' is not bundled with skill '{skill_name}'."
            )
        content = (skill.path / relative_path).read_text(encoding="utf-8")
        return (
            f"<skill_resource skill=\"{skill.name}\" path=\"{relative_path.as_posix()}\">\n"
            f"{content.rstrip()}\n"
            "</skill_resource>"
        )

    read_skill_resource.__annotations__ = {
        "name": skill_name_enum,
        "path": str,
        "return": str,
    }
    return sdk.function_tool(read_skill_resource)


def _maybe_compact_input(
    *,
    sdk: Any,
    model: str,
    input_text: str,
) -> tuple[str, dict[str, Any]]:
    input_tokens = _estimate_tokens(input_text)
    compaction = {
        "threshold_tokens": COMPACTION_TOKEN_THRESHOLD,
        "input_tokens_estimate": input_tokens,
        "input_compacted": False,
        "output_tokens_estimate": 0,
        "output_compacted": False,
    }
    if input_tokens < COMPACTION_TOKEN_THRESHOLD:
        return input_text, compaction

    compacted = _compact_text(
        sdk=sdk,
        model=model,
        text=input_text,
        purpose="workflow input",
    )
    compaction["input_compacted"] = True
    compaction["compacted_input_tokens_estimate"] = _estimate_tokens(compacted)
    wrapped = [
        "The original workflow context exceeded the token budget and was compacted before the main run.",
        "Use the compacted context below as the authoritative summary of the oversized input.",
        "<compacted_workflow_input>",
        compacted,
        "</compacted_workflow_input>",
    ]
    return "\n".join(wrapped), compaction


def _maybe_compact_output(
    *,
    sdk: Any,
    model: str,
    output_text: str,
    compaction: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    output_tokens = _estimate_tokens(output_text)
    compaction["output_tokens_estimate"] = output_tokens
    if output_tokens < COMPACTION_TOKEN_THRESHOLD:
        return output_text, compaction

    compacted = _compact_text(
        sdk=sdk,
        model=model,
        text=output_text,
        purpose="workflow output",
    )
    compaction["output_compacted"] = True
    compaction["compacted_output_tokens_estimate"] = _estimate_tokens(compacted)
    return compacted, compaction


def _compact_text(
    *,
    sdk: Any,
    model: str,
    text: str,
    purpose: str,
) -> str:
    text = _prepare_compaction_source(text)
    compactor = sdk.Agent(
        name="workflow-compactor",
        model=model,
        instructions=(
            "Compact oversized workflow material for later reuse in the same run. "
            "Preserve exact task goals, file paths, run ids, workflow names, agent names, "
            "statuses, concrete commands, action items, blockers, and cited evidence. "
            f"Reduce the content to under {COMPACTION_TARGET_TOKENS} tokens. "
            "Do not add new facts. Prefer short sections and bullet points."
        ),
    )
    result = sdk.Runner.run_sync(
        compactor,
        f"Compact this {purpose}:\n\n{text}",
    )
    return _coerce_final_output(result.final_output)


def _prepare_compaction_source(text: str) -> str:
    if _estimate_tokens(text) <= COMPACTION_SOURCE_MAX_TOKENS:
        return text

    text_length = len(text)
    slice_size = min(60_000, text_length // 4)
    middle_start = max((text_length // 2) - (slice_size // 2), 0)
    middle_end = min(middle_start + slice_size, text_length)
    sampled = [
        "The source was too large to send whole. Compact from these representative windows.",
        "<window label=\"head\">",
        text[:slice_size].rstrip(),
        "</window>",
        "<window label=\"middle\">",
        text[middle_start:middle_end].rstrip(),
        "</window>",
        "<window label=\"tail\">",
        text[-slice_size:].rstrip(),
        "</window>",
    ]
    return "\n".join(sampled)


def _wrap_skill_activation(skill: Skill) -> str:
    lines = [
        f"<skill_content name=\"{skill.name}\">",
        skill.instructions,
        "",
        f"Skill directory: {skill.path}",
        "Relative paths in this skill are relative to the skill directory.",
        "",
    ]
    lines.extend(
        [
            skill.resources.as_wrapped_block(),
            "</skill_content>",
        ]
    )
    return "\n".join(lines)


def _sanitize_enum_member_name(skill_name: str) -> str:
    sanitized = "".join(
        character if character.isalnum() else "_"
        for character in skill_name.upper()
    ).strip("_")
    if not sanitized:
        sanitized = "SKILL"
    if sanitized[0].isdigit():
        sanitized = f"SKILL_{sanitized}"
    return sanitized


def _coerce_final_output(value: Any) -> str:
    if isinstance(value, str):
        return value
    return str(value)


def _estimate_tokens(text: str) -> int:
    try:
        import tiktoken
    except ImportError:
        return math.ceil(len(text) / 4)

    try:
        encoding = tiktoken.get_encoding("o200k_base")
    except Exception:
        return math.ceil(len(text) / 4)
    return len(encoding.encode(text))


def _collect_context_files(project_root: Path, task_input: dict[str, Any]) -> list[str]:
    context_files: list[str] = []
    for value in task_input.values():
        relative_path = _resolve_project_relative_path(project_root, value)
        if relative_path is None:
            continue
        if (project_root / relative_path).is_file():
            context_files.append(relative_path.as_posix())
    return sorted(set(context_files))


def _collect_context_directories(project_root: Path, task_input: dict[str, Any]) -> list[str]:
    context_directories: list[str] = []
    for value in task_input.values():
        relative_path = _resolve_project_relative_path(project_root, value)
        if relative_path is None:
            continue
        if (project_root / relative_path).is_dir():
            context_directories.append(relative_path.as_posix())
    return sorted(set(context_directories))


def _read_text_for_prompt(path: Path, max_chars: int = 12000) -> str:
    text = path.read_text(encoding="utf-8")
    if len(text) <= max_chars:
        return text.rstrip()
    return text[:max_chars].rstrip() + "\n[truncated]"


def _list_directory_for_prompt(path: Path, max_entries: int = 40) -> str:
    entries = sorted(child.name for child in path.iterdir())
    if len(entries) > max_entries:
        entries = entries[:max_entries] + ["[truncated]"]
    return "\n".join(entries)


def _looks_like_context_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if len(value) > 1024 or "\n" in value:
        return False
    return True


def _resolve_project_relative_path(project_root: Path, value: Any) -> Path | None:
    if not _looks_like_context_path(value):
        return None
    try:
        resolved = (project_root / str(value)).resolve()
    except OSError:
        return None

    try:
        return resolved.relative_to(project_root.resolve())
    except ValueError:
        return None


def _load_dotenv(project_root: Path):
    del project_root
    try:
        from dotenv import load_dotenv
    except ImportError:
        return None
    return load_dotenv


def _import_openai_agents_sdk(project_root: Path):
    """
    Import the external `agents` SDK without being shadowed by this repo's
    top-level `agents/` directory.
    """
    with _sanitized_import_path(project_root):
        sys.modules.pop("agents", None)
        sdk = importlib.import_module("agents")
    if getattr(sdk, "Runner", None) is None or getattr(sdk, "Agent", None) is None:
        raise ImportError(
            "Imported 'agents' module does not look like openai-agents. "
            "Ensure the SDK is installed in the selected Python environment."
        )
    return sdk


@contextmanager
def _sanitized_import_path(project_root: Path):
    original = list(sys.path)
    project_root_resolved = project_root.resolve()

    def keep(path_entry: str) -> bool:
        if not path_entry:
            return False
        try:
            return Path(path_entry).resolve() != project_root_resolved
        except OSError:
            return True

    sys.path[:] = [entry for entry in sys.path if keep(entry)]
    try:
        yield
    finally:
        sys.path[:] = original
