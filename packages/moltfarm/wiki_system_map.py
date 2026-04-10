from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable

from .models import Skill
from .storage import write_json, write_text

LESSON_FIELD_PATTERN = re.compile(r"^- `(?P<field>lesson|evidence|scope|reuse)`: (?P<value>.+)$")
TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_-]{2,}")

PROMOTED_INDEX_PATH = Path("wiki/_build/lesson-index.json")
DRAFTS_ROOT = Path("wiki/drafts")

CONFLICT_POSITIVE_MARKERS = (
    "prefer ",
    "use ",
    "start ",
    "keep ",
    "require ",
    "include ",
    "add ",
    "promote ",
    "treat ",
    "make ",
)
CONFLICT_NEGATIVE_MARKERS = (
    "do not ",
    "don't ",
    "avoid ",
    "never ",
    "skip ",
    "forbid ",
    "remove ",
)
TENTATIVE_MARKERS = (
    "pilot",
    "experimental",
    "partial",
    "draft",
    "out of scope",
    "still needs",
    "not yet",
)
STOPWORDS = {
    "about",
    "after",
    "against",
    "also",
    "always",
    "because",
    "before",
    "being",
    "between",
    "build",
    "built",
    "case",
    "cases",
    "change",
    "changes",
    "command",
    "commands",
    "concrete",
    "default",
    "doing",
    "draft",
    "each",
    "explicit",
    "first",
    "from",
    "full",
    "keep",
    "later",
    "lesson",
    "lessons",
    "local",
    "more",
    "only",
    "path",
    "paths",
    "should",
    "skill",
    "skills",
    "that",
    "their",
    "them",
    "then",
    "there",
    "these",
    "they",
    "this",
    "through",
    "when",
    "where",
    "with",
    "without",
    "workflow",
}


@dataclass(frozen=True, slots=True)
class PageDefinition:
    slug: str
    title: str
    description: str
    keywords: tuple[str, ...]
    runtime_paths: tuple[str, ...] = ()
    minimum_lessons: int = 1

    @property
    def relative_path(self) -> str:
        return f"{self.directory}/{self.slug}.md"

    @property
    def directory(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class WorkflowPageDefinition(PageDefinition):
    @property
    def directory(self) -> str:
        return "workflows"


@dataclass(frozen=True, slots=True)
class ComponentPageDefinition(PageDefinition):
    @property
    def directory(self) -> str:
        return "components"


WORKFLOW_PAGE_DEFINITIONS: tuple[WorkflowPageDefinition, ...] = (
    WorkflowPageDefinition(
        slug="author-skill",
        title="Author Skill",
        description="How Molt turns a repo need into a portable local skill with inspectable instructions.",
        keywords=("authoring", "author skill", "skill authoring", "skill instruction", "skill authoring workflow"),
        runtime_paths=(
            "skills/molt-skill-builder-authoring/SKILL.md",
            "README.md",
        ),
    ),
    WorkflowPageDefinition(
        slug="build-evals",
        title="Build Evals",
        description="How Molt drafts or authors canonical eval suites and keeps them reviewable before promotion.",
        keywords=("create-evals", "eval authoring", "draft workspace", "canonical evals", "eval suite"),
        runtime_paths=(
            "packages/moltfarm/eval_authoring.py",
            "README.md",
        ),
    ),
    WorkflowPageDefinition(
        slug="run-evals",
        title="Run Evals",
        description="How Molt runs `eval-skill`, grades results, and interprets benchmark changes.",
        keywords=("eval-skill", "grader", "grading", "benchmark", "comparison", "pass rate", "local evaluator"),
        runtime_paths=(
            "packages/moltfarm/skill_evaluator.py",
            "README.md",
        ),
    ),
    WorkflowPageDefinition(
        slug="inspect-artifacts",
        title="Inspect Artifacts",
        description="How Molt treats runs, logs, traces, and workspace files as the source of truth for review.",
        keywords=("artifact", "artifacts", "trace", "benchmark.json", "feedback.json", "comparison.json", "workspace"),
        runtime_paths=(
            "packages/moltfarm/storage.py",
            "README.md",
        ),
    ),
    WorkflowPageDefinition(
        slug="extract-lessons",
        title="Extract Lessons",
        description="How Molt distills run and eval evidence into reusable lesson files.",
        keywords=("lesson extraction", "extract lessons", "lesson-extractor", "lessons", "run summary"),
        runtime_paths=(
            "skills/lesson-extractor/SKILL.md",
            "README.md",
        ),
    ),
    WorkflowPageDefinition(
        slug="refine-and-rerun",
        title="Refine And Rerun",
        description="How Molt applies lessons back into skills, reruns the same surface, and checks whether behavior improved.",
        keywords=("refine", "refinement", "rerun", "skill improvement", "same concrete input"),
        runtime_paths=(
            "skills/skill-refiner/SKILL.md",
            "README.md",
        ),
    ),
    WorkflowPageDefinition(
        slug="local-model-pilot",
        title="Local Model Pilot",
        description="How Molt validates a direct local-model path first, then layers proxy-backed surfaces and local grading carefully.",
        keywords=("gemma", "llama.cpp", "proxy", "responses", "local model", "openai_compatible", "openai_responses"),
        runtime_paths=(
            "packages/moltfarm/runner.py",
            "Molt-Farm-Proxy/app/main.py",
            "Molt-Farm-Proxy/app/translator.py",
            "README.md",
        ),
    ),
)

COMPONENT_PAGE_DEFINITIONS: tuple[ComponentPageDefinition, ...] = (
    ComponentPageDefinition(
        slug="cli-and-operations",
        title="CLI And Operations",
        description="The small CLI and named operation layer that exposes Molt workflows.",
        keywords=("cli", "command", "skill-builder", "operations.py", "local cli"),
        runtime_paths=(
            "packages/moltfarm/cli.py",
            "packages/moltfarm/operations.py",
        ),
        minimum_lessons=2,
    ),
    ComponentPageDefinition(
        slug="evaluator-and-grading",
        title="Evaluator And Grading",
        description="The evaluator, grader contracts, and benchmark interpretation rules.",
        keywords=("skill_evaluator.py", "grader", "grading", "benchmark", "comparison", "feedback"),
        runtime_paths=(
            "packages/moltfarm/skill_evaluator.py",
            "packages/moltfarm/skill_evals.py",
        ),
        minimum_lessons=2,
    ),
    ComponentPageDefinition(
        slug="local-model-proxy",
        title="Local Model Proxy",
        description="The direct local-model path and the proxy-backed Responses compatibility layer.",
        keywords=("proxy", "responses", "llama.cpp", "ollama", "gemma", "openai_compatible"),
        runtime_paths=(
            "packages/moltfarm/runner.py",
            "Molt-Farm-Proxy/app/main.py",
            "Molt-Farm-Proxy/app/ollama_client.py",
            "Molt-Farm-Proxy/app/translator.py",
        ),
        minimum_lessons=2,
    ),
    ComponentPageDefinition(
        slug="skill-instructions",
        title="Skill Instructions",
        description="The portable `SKILL.md` layer where repo-specific guidance should live.",
        keywords=("skill instructions", "skill-backed", "SKILL.md", "instruction phrasing", "authoring-loop"),
        runtime_paths=(
            "skills/skill-refiner/SKILL.md",
            "skills/molt-skill-builder-authoring/SKILL.md",
            "skills/llm-wiki/SKILL.md",
        ),
        minimum_lessons=2,
    ),
    ComponentPageDefinition(
        slug="testing-and-evidence",
        title="Testing And Evidence",
        description="How tests, traces, and file-backed artifacts validate changes without hiding the evidence.",
        keywords=("pytest", "coverage", "trace", "artifact", "evidence", "tests"),
        runtime_paths=(
            "README.md",
            "tests",
        ),
        minimum_lessons=2,
    ),
    ComponentPageDefinition(
        slug="wiki-authoring",
        title="Wiki Authoring",
        description="The evidence discipline and taxonomy rules for turning notes into curated wiki pages.",
        keywords=("wiki", "llm-wiki", "taxonomy", "canonical page", "source-path"),
        runtime_paths=(
            "skills/llm-wiki/SKILL.md",
            "skills/llm-wiki-validator/SKILL.md",
        ),
        minimum_lessons=2,
    ),
)

WORKFLOW_PAGES_BY_SLUG = {page.slug: page for page in WORKFLOW_PAGE_DEFINITIONS}
COMPONENT_PAGES_BY_SLUG = {page.slug: page for page in COMPONENT_PAGE_DEFINITIONS}


@dataclass(slots=True)
class LessonEntry:
    source_path: str
    title: str
    lesson: str
    evidence: str
    scope: str
    reuse: str
    section_title: str
    supporting_paths: list[str] = field(default_factory=list)
    workflow_pages: list[str] = field(default_factory=list)
    component_pages: list[str] = field(default_factory=list)
    claim_status: str = "stable"

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "source_path": self.source_path,
            "title": self.title,
            "lesson": self.lesson,
            "evidence": self.evidence,
            "scope": self.scope,
            "reuse": self.reuse,
            "workflow_pages": list(self.workflow_pages),
            "component_pages": list(self.component_pages),
            "claim_status": self.claim_status,
            "supporting_paths": list(self.supporting_paths),
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "LessonEntry":
        return cls(
            source_path=str(payload.get("source_path") or ""),
            title=str(payload.get("title") or ""),
            lesson=str(payload.get("lesson") or ""),
            evidence=str(payload.get("evidence") or ""),
            scope=str(payload.get("scope") or ""),
            reuse=str(payload.get("reuse") or ""),
            section_title=str(payload.get("section_title") or payload.get("title") or ""),
            supporting_paths=[str(item) for item in payload.get("supporting_paths") or []],
            workflow_pages=[str(item) for item in payload.get("workflow_pages") or []],
            component_pages=[str(item) for item in payload.get("component_pages") or []],
            claim_status=str(payload.get("claim_status") or "stable"),
        )


def draft_system_map(
    project_root: Path,
    *,
    lesson_paths: str = "",
    lesson_glob: str = "lessons/*.md",
    workflow_focus: str = "",
    date_from: str = "",
    date_to: str = "",
) -> dict[str, Any]:
    selected_workflows = _normalize_workflow_focus(workflow_focus)
    resolved_lesson_paths = _resolve_lesson_paths(
        project_root=project_root,
        explicit_paths=lesson_paths,
        lesson_glob=lesson_glob,
        date_from=date_from,
        date_to=date_to,
    )
    entries = _build_lesson_entries(
        project_root=project_root,
        lesson_paths=resolved_lesson_paths,
        workflow_focus=selected_workflows,
    )
    draft_root = project_root / DRAFTS_ROOT
    draft_root.mkdir(parents=True, exist_ok=True)
    session_dir = _create_draft_session_dir(draft_root)
    session_id = session_dir.name
    draft_pages_root = session_dir / "pages"
    written_page_paths = _write_page_set(
        project_root=project_root,
        target_root=draft_pages_root,
        entries=entries,
        workflow_focus=selected_workflows,
        include_promoted_index_link=False,
        draft_mode=True,
    )
    draft_index_path = write_json(
        session_dir / "_build" / "lesson-index.json",
        {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "entries": [entry.to_public_dict() for entry in entries],
        },
    )
    plan_path = write_text(
        session_dir / "plan.md",
        _render_plan_markdown(
            entries=entries,
            lesson_paths=[str(path.relative_to(project_root)) for path in resolved_lesson_paths],
            workflow_focus=selected_workflows,
            session_id=session_id,
        ),
    )
    session_path = write_json(
        session_dir / "session.json",
        {
            "session_id": session_id,
            "phase": "draft_ready",
            "status": "completed",
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "filters": {
                "lesson_paths": _split_csv(lesson_paths),
                "lesson_glob": lesson_glob,
                "workflow_focus": selected_workflows,
                "date_from": date_from,
                "date_to": date_to,
            },
            "lesson_count": len(resolved_lesson_paths),
            "entry_count": len(entries),
            "draft_plan_path": str(plan_path.relative_to(project_root)),
            "draft_index_path": str(draft_index_path.relative_to(project_root)),
            "draft_page_paths": written_page_paths,
        },
    )
    return {
        "summary": (
            f"Drafted workflow-first system map session {session_id} from "
            f"{len(resolved_lesson_paths)} lesson files."
        ),
        "draft_session_id": session_id,
        "draft_session_path": str(session_dir.relative_to(project_root)),
        "draft_plan_path": str(plan_path.relative_to(project_root)),
        "draft_index_path": str(draft_index_path.relative_to(project_root)),
        "draft_page_paths": written_page_paths,
        "lesson_count": len(resolved_lesson_paths),
        "entry_count": len(entries),
        "context_files": [str(path.relative_to(project_root)) for path in resolved_lesson_paths],
        "metadata_path": str(session_path.relative_to(project_root)),
    }


def promote_system_map(project_root: Path, *, session_id: str) -> dict[str, Any]:
    session_dir = project_root / DRAFTS_ROOT / session_id
    session_path = session_dir / "session.json"
    if not session_path.is_file():
        raise ValueError(f"System-map session '{session_id}' was not found.")

    session = _read_json(session_path)
    draft_index_path = session_dir / "_build" / "lesson-index.json"
    if not draft_index_path.is_file():
        raise ValueError(f"System-map session '{session_id}' is missing its draft lesson index.")

    payload = _read_json(draft_index_path)
    entries = [LessonEntry.from_payload(item) for item in payload.get("entries") or []]
    workflow_focus = [str(item) for item in (session.get("filters", {}).get("workflow_focus") or [])]
    written_page_paths = _write_page_set(
        project_root=project_root,
        target_root=project_root / "wiki",
        entries=entries,
        workflow_focus=workflow_focus,
        include_promoted_index_link=True,
        draft_mode=False,
    )
    promoted_index_path = write_json(
        project_root / PROMOTED_INDEX_PATH,
        {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "session_id": session_id,
            "entries": [entry.to_public_dict() for entry in entries],
        },
    )
    session["phase"] = "promoted"
    session["status"] = "completed"
    session["promoted_at"] = datetime.now().isoformat(timespec="seconds")
    session["promoted_page_paths"] = written_page_paths
    session["promoted_index_path"] = str(promoted_index_path.relative_to(project_root))
    write_json(session_path, session)
    return {
        "session_id": session_id,
        "status": "completed",
        "promoted_index_path": str(promoted_index_path.relative_to(project_root)),
        "promoted_page_paths": written_page_paths,
        "summary": f"Promoted workflow-first system map session {session_id} into wiki/.",
    }


def find_relevant_lessons(
    project_root: Path,
    *,
    skill: Skill,
    max_results: int = 4,
) -> list[dict[str, str]]:
    promoted_matches = _find_relevant_promoted_entries(
        project_root=project_root,
        skill=skill,
        max_results=max_results,
    )
    if promoted_matches:
        return promoted_matches
    return _find_relevant_raw_lessons(project_root=project_root, skill=skill, max_results=max_results)


def find_relevant_lesson_paths(
    project_root: Path,
    *,
    skill: Skill,
    max_results: int = 4,
) -> list[str]:
    return [item["path"] for item in find_relevant_lessons(project_root, skill=skill, max_results=max_results)]


def _resolve_lesson_paths(
    *,
    project_root: Path,
    explicit_paths: str,
    lesson_glob: str,
    date_from: str,
    date_to: str,
) -> list[Path]:
    selected_paths: list[Path] = []
    if explicit_paths.strip():
        for raw_path in _split_csv(explicit_paths):
            resolved = (project_root / raw_path).resolve()
            try:
                resolved.relative_to(project_root.resolve())
            except ValueError as exc:
                raise ValueError(f"Lesson path '{raw_path}' escapes the project root.") from exc
            if not resolved.is_file():
                raise ValueError(f"Lesson path '{raw_path}' was not found.")
            selected_paths.append(resolved)
    else:
        selected_paths.extend(sorted((project_root / ".").glob(lesson_glob)))

    filtered: list[Path] = []
    lower_bound = _parse_optional_date(date_from)
    upper_bound = _parse_optional_date(date_to)
    for path in selected_paths:
        if not path.is_file() or path.suffix.lower() != ".md":
            continue
        lesson_date = _date_from_lesson_filename(path.name)
        if lower_bound and lesson_date and lesson_date < lower_bound:
            continue
        if upper_bound and lesson_date and lesson_date > upper_bound:
            continue
        filtered.append(path.resolve())
    if not filtered:
        raise ValueError("No lesson files matched the current system-map draft filters.")
    return sorted(dict.fromkeys(filtered))


def _build_lesson_entries(
    *,
    project_root: Path,
    lesson_paths: list[Path],
    workflow_focus: list[str],
) -> list[LessonEntry]:
    entries: list[LessonEntry] = []
    for lesson_path in lesson_paths:
        entries.extend(_parse_lesson_file(project_root=project_root, lesson_path=lesson_path))

    for entry in entries:
        entry.workflow_pages = _match_page_paths(entry, page_definitions=WORKFLOW_PAGE_DEFINITIONS)

    available_workflows = set(workflow_focus) if workflow_focus else None
    if available_workflows is not None:
        entries = [
            entry
            for entry in entries
            if any(path.split("/", 1)[1].rsplit(".", 1)[0] in available_workflows for path in entry.workflow_pages)
        ]

    component_counts: dict[str, int] = {}
    component_matches: dict[int, list[str]] = {}
    for index, entry in enumerate(entries):
        matched = _match_page_paths(entry, page_definitions=COMPONENT_PAGE_DEFINITIONS)
        component_matches[index] = matched
        for path in matched:
            component_counts[path] = component_counts.get(path, 0) + 1

    for index, entry in enumerate(entries):
        filtered_components: list[str] = []
        for path in component_matches[index]:
            component = COMPONENT_PAGES_BY_SLUG[path.split("/", 1)[1].rsplit(".", 1)[0]]
            if component_counts.get(path, 0) >= component.minimum_lessons:
                filtered_components.append(path)
        entry.component_pages = filtered_components
        entry.claim_status = _determine_claim_status(entry, entries)

    return sorted(entries, key=lambda item: (item.source_path, item.title, item.lesson))


def _parse_lesson_file(*, project_root: Path, lesson_path: Path) -> list[LessonEntry]:
    text = lesson_path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = next((line[2:].strip() for line in lines if line.startswith("# ")), lesson_path.stem)
    source_lines = _extract_source_lines(lines)
    supporting_paths = _extract_supporting_paths("\n".join(source_lines))

    current_section = "Overview"
    pending: dict[str, str] = {}
    entries: list[LessonEntry] = []
    for line in lines:
        if line.startswith("## "):
            current_section = line[3:].strip()
            continue
        match = LESSON_FIELD_PATTERN.match(line)
        if not match:
            continue
        field = match.group("field")
        pending[field] = match.group("value").strip()
        if {"lesson", "evidence", "scope", "reuse"}.issubset(pending):
            entries.append(
                LessonEntry(
                    source_path=str(lesson_path.relative_to(project_root)),
                    title=f"{title}: {current_section}",
                    lesson=pending["lesson"],
                    evidence=pending["evidence"],
                    scope=pending["scope"],
                    reuse=pending["reuse"],
                    section_title=current_section,
                    supporting_paths=list(supporting_paths),
                )
            )
            pending = {}
    return entries


def _extract_source_lines(lines: list[str]) -> list[str]:
    collected: list[str] = []
    in_source = False
    for line in lines:
        if line.strip() == "Source:":
            in_source = True
            continue
        if in_source and line.startswith("## "):
            break
        if in_source:
            collected.append(line)
    return collected


def _extract_supporting_paths(text: str) -> list[str]:
    matches = re.findall(r"`([^`]+)`", text)
    paths: list[str] = []
    for match in matches:
        if "/" not in match and not any(match.endswith(suffix) for suffix in (".md", ".py", ".json", ".yaml", ".txt")):
            continue
        paths.append(match)
    return sorted(dict.fromkeys(paths))


def _match_page_paths(entry: LessonEntry, *, page_definitions: Iterable[PageDefinition]) -> list[str]:
    haystack = _entry_haystack(entry)
    matches: list[str] = []
    for page in page_definitions:
        if any(keyword in haystack for keyword in page.keywords):
            matches.append(page.relative_path)
    return matches


def _determine_claim_status(entry: LessonEntry, all_entries: list[LessonEntry]) -> str:
    haystack = _entry_haystack(entry)
    if any(marker in haystack for marker in TENTATIVE_MARKERS):
        tentative = True
    else:
        tentative = False

    entry_tokens = _meaningful_tokens(f"{entry.scope} {entry.lesson}")
    entry_direction = _conflict_direction(f"{entry.lesson} {entry.reuse}")
    if entry_direction == "neutral":
        return "tentative" if tentative else "stable"

    for candidate in all_entries:
        if candidate is entry:
            continue
        if candidate.scope.strip().lower() != entry.scope.strip().lower():
            continue
        candidate_direction = _conflict_direction(f"{candidate.lesson} {candidate.reuse}")
        if candidate_direction == "neutral" or candidate_direction == entry_direction:
            continue
        overlap = entry_tokens.intersection(_meaningful_tokens(f"{candidate.scope} {candidate.lesson}"))
        if len(overlap) >= 3:
            return "conflict"
    return "tentative" if tentative else "stable"


def _write_page_set(
    *,
    project_root: Path,
    target_root: Path,
    entries: list[LessonEntry],
    workflow_focus: list[str],
    include_promoted_index_link: bool,
    draft_mode: bool,
) -> list[str]:
    target_root.mkdir(parents=True, exist_ok=True)
    written_paths: list[str] = []

    workflows_to_render = [
        page
        for page in WORKFLOW_PAGE_DEFINITIONS
        if not workflow_focus or page.slug in workflow_focus
    ]
    for page in workflows_to_render:
        page_entries = [entry for entry in entries if page.relative_path in entry.workflow_pages]
        content = _render_topic_page(
            project_root=project_root,
            target_root=target_root,
            page=page,
            entries=page_entries,
            draft_mode=draft_mode,
        )
        written_paths.append(
            str(write_text(target_root / page.relative_path, content).relative_to(project_root))
        )

    components_to_render = []
    for page in COMPONENT_PAGE_DEFINITIONS:
        page_entries = [entry for entry in entries if page.relative_path in entry.component_pages]
        if not page_entries:
            continue
        components_to_render.append(page)
        content = _render_topic_page(
            project_root=project_root,
            target_root=target_root,
            page=page,
            entries=page_entries,
            draft_mode=draft_mode,
        )
        written_paths.append(
            str(write_text(target_root / page.relative_path, content).relative_to(project_root))
        )

    index_content = _render_index_page(
        project_root=project_root,
        target_root=target_root,
        entries=entries,
        workflows=workflows_to_render,
        components=components_to_render,
        include_promoted_index_link=include_promoted_index_link,
        draft_mode=draft_mode,
    )
    written_paths.append(str(write_text(target_root / "index.md", index_content).relative_to(project_root)))
    return sorted(written_paths)


def _render_index_page(
    *,
    project_root: Path,
    target_root: Path,
    entries: list[LessonEntry],
    workflows: list[WorkflowPageDefinition],
    components: list[ComponentPageDefinition],
    include_promoted_index_link: bool,
    draft_mode: bool,
) -> str:
    lines = [
        "# Molt System Map",
        "",
        "Workflow-first guide to the current Molt loop, built from durable lesson files.",
        "",
        "## Primary Workflows",
    ]
    for page in workflows:
        page_entry_count = sum(1 for entry in entries if page.relative_path in entry.workflow_pages)
        lines.append(
            f"- {_render_link(target_root / 'index.md', target_root / page.relative_path, page.title)}"
            f": {page.description} ({page_entry_count} lesson items)"
        )

    if components:
        lines.extend(["", "## Components"])
        for page in components:
            page_entry_count = sum(1 for entry in entries if page.relative_path in entry.component_pages)
            lines.append(
                f"- {_render_link(target_root / 'index.md', target_root / page.relative_path, page.title)}"
                f": {page.description} ({page_entry_count} lesson items)"
            )

    lines.extend(
        [
            "",
            "## Raw Lesson Files",
            f"- Source corpus size: {len(sorted({entry.source_path for entry in entries}))} files / {len(entries)} lesson items",
        ]
    )
    for source_path in sorted({entry.source_path for entry in entries})[:12]:
        lines.append(
            f"- {_render_link(target_root / 'index.md', project_root / source_path, source_path)}"
        )

    lines.extend(["", "## Promotion Model"])
    lines.append("- Draft sessions live under `wiki/drafts/session-N/` and stay reviewable until promotion.")
    if include_promoted_index_link:
        lines.append(
            f"- Promoted lesson index: {_render_link(target_root / 'index.md', project_root / PROMOTED_INDEX_PATH, str(PROMOTED_INDEX_PATH))}"
        )
    else:
        lines.append("- Promotion refreshes `wiki/_build/lesson-index.json` without rewriting raw lesson files.")
    return "\n".join(lines) + "\n"


def _render_topic_page(
    *,
    project_root: Path,
    target_root: Path,
    page: PageDefinition,
    entries: list[LessonEntry],
    draft_mode: bool,
) -> str:
    page_path = target_root / page.relative_path
    lines = [
        f"# {page.title}",
        "",
        page.description,
        "",
        "## Working Guidance",
    ]
    if not entries:
        lines.append("- No lesson items matched the current filters for this page.")
    else:
        stable_entries = [entry for entry in entries if entry.claim_status == "stable"]
        tentative_entries = [entry for entry in entries if entry.claim_status == "tentative"]
        conflict_entries = [entry for entry in entries if entry.claim_status == "conflict"]
        if stable_entries:
            lines.append("### Stable")
            lines.extend(_render_entry_bullets(page_path=page_path, project_root=project_root, entries=stable_entries, draft_mode=draft_mode))
        if tentative_entries:
            lines.extend(["", "### Tentative"])
            lines.extend(_render_entry_bullets(page_path=page_path, project_root=project_root, entries=tentative_entries, draft_mode=draft_mode))
        if conflict_entries:
            lines.extend(["", "### Conflicts To Resolve"])
            lines.extend(_render_entry_bullets(page_path=page_path, project_root=project_root, entries=conflict_entries, draft_mode=draft_mode))

    runtime_paths = _page_runtime_paths(page=page, entries=entries, project_root=project_root)
    if runtime_paths:
        lines.extend(["", "## Relevant Runtime Surfaces"])
        for runtime_path in runtime_paths:
            lines.append(
                f"- {_render_link(page_path, project_root / runtime_path, runtime_path)}"
            )

    lines.extend(["", "## Supporting Lesson Files"])
    for source_path in sorted({entry.source_path for entry in entries}):
        lines.append(
            f"- {_render_link(page_path, project_root / source_path, source_path)}"
        )
    return "\n".join(lines) + "\n"


def _render_entry_bullets(
    *,
    page_path: Path,
    project_root: Path,
    entries: list[LessonEntry],
    draft_mode: bool,
) -> list[str]:
    lines: list[str] = []
    for entry in entries:
        lines.append(
            f"- {entry.lesson} Supporting lesson: "
            f"{_render_link(page_path, project_root / entry.source_path, entry.source_path)}"
        )
        lines.append(f"  Evidence: {entry.evidence}")
        lines.append(f"  Reuse: {entry.reuse}")
    return lines


def _page_runtime_paths(
    *,
    page: PageDefinition,
    entries: list[LessonEntry],
    project_root: Path,
) -> list[str]:
    paths: list[str] = []
    for runtime_path in page.runtime_paths:
        if (project_root / runtime_path).exists():
            paths.append(runtime_path)
    for entry in entries:
        for supporting_path in entry.supporting_paths:
            if supporting_path.startswith("runs/") or supporting_path.startswith("logs/"):
                continue
            if (project_root / supporting_path).exists():
                paths.append(supporting_path)
    return list(dict.fromkeys(paths))[:8]


def _render_plan_markdown(
    *,
    entries: list[LessonEntry],
    lesson_paths: list[str],
    workflow_focus: list[str],
    session_id: str,
) -> str:
    workflow_counts: dict[str, int] = {}
    component_counts: dict[str, int] = {}
    for entry in entries:
        for workflow_path in entry.workflow_pages:
            workflow_counts[workflow_path] = workflow_counts.get(workflow_path, 0) + 1
        for component_path in entry.component_pages:
            component_counts[component_path] = component_counts.get(component_path, 0) + 1

    lines = [
        f"# System Map Draft Plan: {session_id}",
        "",
        "## Inputs",
        f"- Lesson files: {len(lesson_paths)}",
        f"- Workflow focus: {', '.join(workflow_focus) if workflow_focus else 'all workflows'}",
        "",
        "## Included Lesson Files",
    ]
    for lesson_path in lesson_paths:
        lines.append(f"- `{lesson_path}`")
    lines.extend(["", "## Candidate Workflow Pages"])
    for workflow_path, count in sorted(workflow_counts.items()):
        lines.append(f"- `{workflow_path}` from {count} lesson items")
    if not workflow_counts:
        lines.append("- none")
    lines.extend(["", "## Candidate Component Pages"])
    for component_path, count in sorted(component_counts.items()):
        lines.append(f"- `{component_path}` from {count} lesson items")
    if not component_counts:
        lines.append("- none")
    conflict_count = sum(1 for entry in entries if entry.claim_status == "conflict")
    tentative_count = sum(1 for entry in entries if entry.claim_status == "tentative")
    lines.extend(
        [
            "",
            "## Review Notes",
            f"- Conflict items: {conflict_count}",
            f"- Tentative items: {tentative_count}",
            "- Promotion writes canonical pages under `wiki/` and refreshes `wiki/_build/lesson-index.json`.",
        ]
    )
    return "\n".join(lines) + "\n"


def _find_relevant_promoted_entries(
    *,
    project_root: Path,
    skill: Skill,
    max_results: int,
) -> list[dict[str, str]]:
    index_path = project_root / PROMOTED_INDEX_PATH
    if not index_path.is_file():
        return []
    payload = _read_json(index_path)
    entries = [LessonEntry.from_payload(item) for item in payload.get("entries") or []]
    scored: list[tuple[int, LessonEntry]] = []
    exact_targets = {skill.name.lower(), f"skills/{skill.name}/".lower()}
    token_targets = _meaningful_tokens(f"{skill.name} {skill.description}")
    for entry in entries:
        haystack = _entry_haystack(entry)
        score = 0
        for target in exact_targets:
            if target in haystack:
                score += 12
        supporting_text = " ".join(entry.supporting_paths).lower()
        for target in exact_targets:
            if target in supporting_text:
                score += 20
        overlap = token_targets.intersection(_meaningful_tokens(haystack))
        score += min(len(overlap), 6)
        if score:
            scored.append((score, entry))
    if not scored:
        return []

    grouped: dict[str, list[LessonEntry]] = {}
    for _, entry in sorted(scored, key=lambda item: (-item[0], item[1].source_path, item[1].title)):
        grouped.setdefault(entry.source_path, []).append(entry)

    results: list[dict[str, str]] = []
    for source_path, grouped_entries in grouped.items():
        excerpt_lines = []
        for entry in grouped_entries[:2]:
            excerpt_lines.extend(
                [
                    entry.title,
                    f"- lesson: {entry.lesson}",
                    f"- scope: {entry.scope}",
                    f"- reuse: {entry.reuse}",
                ]
            )
        results.append({"path": source_path, "excerpt": "\n".join(excerpt_lines)})
        if len(results) >= max_results:
            break
    return results


def _find_relevant_raw_lessons(
    *,
    project_root: Path,
    skill: Skill,
    max_results: int,
) -> list[dict[str, str]]:
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
                "path": str(lesson_path.relative_to(project_root)),
                "excerpt": _truncate_text(text, max_chars=3000),
            }
        )
    return matches[:max_results]


def _entry_haystack(entry: LessonEntry) -> str:
    return " ".join(
        [
            entry.source_path,
            entry.title,
            entry.lesson,
            entry.evidence,
            entry.scope,
            entry.reuse,
            " ".join(entry.supporting_paths),
            " ".join(entry.workflow_pages),
            " ".join(entry.component_pages),
        ]
    ).lower()


def _truncate_text(text: str, *, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def _conflict_direction(text: str) -> str:
    lowered = text.lower()
    if any(marker in lowered for marker in CONFLICT_NEGATIVE_MARKERS):
        return "negative"
    if any(marker in lowered for marker in CONFLICT_POSITIVE_MARKERS):
        return "positive"
    return "neutral"


def _meaningful_tokens(text: str) -> set[str]:
    return {
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if token not in STOPWORDS
    }


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalize_workflow_focus(value: str) -> list[str]:
    requested = _split_csv(value)
    if not requested:
        return []
    unknown = [item for item in requested if item not in WORKFLOW_PAGES_BY_SLUG]
    if unknown:
        raise ValueError(
            "Unknown workflow_focus value(s): "
            + ", ".join(sorted(unknown))
            + ". Expected one of: "
            + ", ".join(sorted(WORKFLOW_PAGES_BY_SLUG))
        )
    return requested


def _create_draft_session_dir(draft_root: Path) -> Path:
    existing_numbers = []
    for child in draft_root.iterdir():
        if child.is_dir() and re.fullmatch(r"session-\d+", child.name):
            existing_numbers.append(int(child.name.split("-")[1]))
    next_number = max(existing_numbers, default=0) + 1
    session_dir = draft_root / f"session-{next_number}"
    session_dir.mkdir(parents=True, exist_ok=False)
    return session_dir


def _render_link(page_path: Path, target_path: Path, label: str) -> str:
    relative = _relative_link(page_path.parent, target_path)
    return f"[{label}]({relative})"


def _relative_link(source_dir: Path, target_path: Path) -> str:
    return Path(os.path.relpath(target_path, start=source_dir)).as_posix()


def _parse_optional_date(value: str) -> date | None:
    raw = value.strip()
    if not raw:
        return None
    return date.fromisoformat(raw)


def _date_from_lesson_filename(filename: str) -> date | None:
    match = re.match(r"(?P<date>\d{4}-\d{2}-\d{2})-", filename)
    if not match:
        return None
    return date.fromisoformat(match.group("date"))


def _read_json(path: Path) -> dict[str, Any]:
    import json

    return json.loads(path.read_text(encoding="utf-8"))
