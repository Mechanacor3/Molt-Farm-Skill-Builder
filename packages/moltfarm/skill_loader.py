from __future__ import annotations

import re
from pathlib import Path

import yaml

from .models import Skill, SkillResources

REFERENCE_PATTERN = re.compile(r"(?P<ref>@\./[A-Za-z0-9_./-]+)")


def discover_skills(skills_root: Path) -> dict[str, Skill]:
    """Load skills from any nested directory under the configured skills root."""
    skills: dict[str, Skill] = {}
    if not skills_root.exists():
        return skills

    skill_files = sorted(
        skill_file
        for skill_file in skills_root.rglob("SKILL.md")
        if skill_file.is_file() and not _is_generated_skill_artifact(skill_file, skills_root)
    )
    for skill_file in skill_files:
        skill = load_skill(skill_file)
        skills[skill.name] = skill
    return skills


def load_skill(skill_file: Path) -> Skill:
    raw_text = skill_file.read_text(encoding="utf-8")
    metadata, instructions = _split_frontmatter(raw_text)
    name = metadata.get("name") or skill_file.parent.name
    description = metadata.get("description") or "No description provided."
    resources = _collect_resources(skill_file.parent)
    expanded_instructions, referenced_paths = _expand_references(
        instructions=instructions.strip(),
        skill_dir=skill_file.parent,
    )
    return Skill(
        name=name,
        description=description,
        path=skill_file.parent,
        instructions=expanded_instructions,
        referenced_paths=referenced_paths,
        resources=resources,
    )


def _split_frontmatter(raw_text: str) -> tuple[dict[str, str], str]:
    if not raw_text.startswith("---\n"):
        return {}, raw_text

    parts = raw_text.split("---\n", 2)
    if len(parts) < 3:
        return {}, raw_text

    _, frontmatter, body = parts
    metadata = yaml.safe_load(frontmatter) or {}
    if not isinstance(metadata, dict):
        return {}, body
    return metadata, body


def _expand_references(instructions: str, skill_dir: Path) -> tuple[str, list[Path]]:
    """
    Inline referenced files using the Codex-style @./relative/path convention.

    We keep resolution local to the skill directory so a skill cannot silently
    pull unrelated repository files into context.
    """
    referenced_paths: list[Path] = []

    def replace(match: re.Match[str]) -> str:
        token = match.group("ref")
        relative_path = token[1:]
        resolved_path = (skill_dir / relative_path).resolve()
        root_path = skill_dir.resolve()

        try:
            resolved_path.relative_to(root_path)
        except ValueError as exc:
            raise ValueError(f"Skill reference escapes skill directory: {token}") from exc

        if not resolved_path.is_file():
            raise FileNotFoundError(f"Referenced skill file not found: {token}")

        referenced_paths.append(resolved_path.relative_to(root_path))
        content = resolved_path.read_text(encoding="utf-8").strip()
        return (
            f"{token}\n"
            f"<referenced-file path=\"{referenced_paths[-1].as_posix()}\">\n"
            f"{content}\n"
            f"</referenced-file>"
        )

    return REFERENCE_PATTERN.sub(replace, instructions), referenced_paths


def _collect_resources(skill_dir: Path) -> SkillResources:
    resource_index = SkillResources()
    resource_files = sorted(
        (path for path in skill_dir.rglob("*") if path.is_file()),
        key=lambda path: (len(path.relative_to(skill_dir).parts), path.relative_to(skill_dir).as_posix()),
    )
    for file_path in resource_files:
        if file_path.name == "SKILL.md":
            continue
        relative_path = file_path.relative_to(skill_dir)
        category = _resource_category(relative_path)
        getattr(resource_index, category).append(relative_path)
    return resource_index


def _is_generated_skill_artifact(skill_file: Path, skills_root: Path) -> bool:
    try:
        relative = skill_file.relative_to(skills_root)
    except ValueError:
        return False
    parts = relative.parts
    for index in range(len(parts) - 1):
        if parts[index] == "evals" and index + 1 < len(parts) and parts[index + 1] == "workspace":
            return True
    return False


def _resource_category(relative_path: Path) -> str:
    parts = relative_path.parts
    if not parts:
        return "other"

    top_level = parts[0]
    if top_level in {"scripts", "references", "assets", "examples", "agents"}:
        return top_level
    return "other"
