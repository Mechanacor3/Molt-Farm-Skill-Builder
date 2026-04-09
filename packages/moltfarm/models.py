from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class EvalCheck:
    text: str
    category: str = "goal"
    weight: float = 1.0


@dataclass(slots=True)
class SkillResources:
    scripts: list[Path] = field(default_factory=list)
    references: list[Path] = field(default_factory=list)
    assets: list[Path] = field(default_factory=list)
    examples: list[Path] = field(default_factory=list)
    agents: list[Path] = field(default_factory=list)
    other: list[Path] = field(default_factory=list)

    def as_wrapped_block(self) -> str:
        """Render a structured resource listing for activation-tool responses."""
        lines = ["<skill_resources>"]
        for category, paths in self.iter_categories():
            for path in paths:
                lines.append(f'  <file category="{category}">{path.as_posix()}</file>')
        lines.append("</skill_resources>")
        return "\n".join(lines)

    def iter_categories(self) -> list[tuple[str, list[Path]]]:
        return [
            ("scripts", self.scripts),
            ("references", self.references),
            ("assets", self.assets),
            ("examples", self.examples),
            ("agents", self.agents),
            ("other", self.other),
        ]


@dataclass(slots=True)
class Skill:
    name: str
    description: str
    path: Path
    instructions: str
    referenced_paths: list[Path] = field(default_factory=list)
    resources: SkillResources = field(default_factory=SkillResources)


@dataclass(slots=True)
class SkillEvalCase:
    case_id: str
    prompt: str
    expected_output: str
    files: list[Path] = field(default_factory=list)
    checks: list[EvalCheck] = field(default_factory=list)
    required_skill_activations: list[str] = field(default_factory=list)


@dataclass(slots=True)
class SkillEvalSuite:
    skill_name: str
    evals_path: Path
    cases: list[SkillEvalCase] = field(default_factory=list)


@dataclass(slots=True)
class AgentDefinition:
    name: str
    description: str
    model: str
    skills: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    context_policy: str = "least_context"
    runtime: str = "stub"
    path: Path | None = None


@dataclass(slots=True)
class ResolvedModelConfig:
    role: str
    provider: str
    model: str
    api_surface: str = "native"
    base_url: str | None = None
    api_key: str | None = None


@dataclass(slots=True)
class OperationDefinition:
    name: str
    description: str
    agent: AgentDefinition
    inputs: dict[str, Any] = field(default_factory=dict)
    logging_policy: str = "per_run"
    execution_policy: str = "local"


@dataclass(slots=True)
class RunResult:
    run_id: str
    workflow: str
    agent: str
    status: str
    inputs: dict[str, Any]
    output: dict[str, Any]
    log_path: str
    run_path: str
