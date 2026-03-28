from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
from pathlib import Path
from typing import Any

from ..skill_loader import DiscoveredSkillRecord, discover_skill_records
from ..storage import write_json

ANALYSIS_VERSION = 1
NEAR_DUPE_THRESHOLD = 0.50
HIGH_SEVERITY_THRESHOLD = 0.70
SAME_NAME_SCORE_FLOOR = 0.85
TRIGGER_SECTION_PATTERN = re.compile(
    r"Use this skill when:\s*(?P<trigger>.*?)(?:\n\s*Instructions:\s*|\Z)",
    re.IGNORECASE | re.DOTALL,
)
INSTRUCTION_SECTION_PATTERN = re.compile(
    r"Instructions:\s*(?P<body>.*)\Z",
    re.IGNORECASE | re.DOTALL,
)
TOKEN_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.IGNORECASE)
LINE_PREFIX_PATTERN = re.compile(r"^(?:[-*]\s+|\d+\.\s+)")
STOPWORDS = {
    "a",
    "about",
    "after",
    "all",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "but",
    "by",
    "do",
    "does",
    "for",
    "from",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "keep",
    "local",
    "main",
    "make",
    "needs",
    "next",
    "not",
    "of",
    "on",
    "or",
    "over",
    "prefer",
    "repo",
    "should",
    "skill",
    "skills",
    "small",
    "so",
    "stay",
    "task",
    "tasks",
    "that",
    "the",
    "their",
    "then",
    "this",
    "to",
    "use",
    "user",
    "using",
    "want",
    "when",
    "with",
    "work",
    "you",
    "your",
}
DISAMBIGUATION_HINTS = (
    "only",
    "prefer",
    "instead",
    "after",
    "before",
    "already",
    "stable",
    "playable",
    "broken",
    "broad",
    "generic",
    "rather than",
    "not the whole",
    "switch",
    "last",
)


@dataclass(slots=True)
class SkillTextProfile:
    record: DiscoveredSkillRecord
    name_terms: Counter[str]
    description_terms: Counter[str]
    trigger_terms: Counter[str]
    body_terms: Counter[str]
    combined_terms: Counter[str]
    cue_lines: list[str]


def analyze_skill_near_dupes(
    skills_root: Path,
    *,
    areas: list[str] | None = None,
) -> dict[str, Any]:
    resolved_skills_root = skills_root.resolve()
    if not resolved_skills_root.is_dir():
        raise FileNotFoundError(f"Skills root not found: {resolved_skills_root}")

    records = discover_skill_records(resolved_skills_root)
    available_areas = sorted({record.area for record in records})
    selected_areas = _select_areas(areas=areas, available_areas=available_areas)
    selected_area_set = set(selected_areas)
    filtered_records = [record for record in records if record.area in selected_area_set]
    profiles = [_build_profile(record) for record in filtered_records]

    pairs: list[dict[str, Any]] = []
    for left_profile, right_profile in combinations(profiles, 2):
        pair = _build_pair(left_profile, right_profile)
        if pair is not None:
            pairs.append(pair)

    pairs.sort(
        key=lambda pair: (
            -float(pair["score"]),
            str(pair["left"]["path"]),
            str(pair["right"]["path"]),
            str(pair["left"]["name"]),
            str(pair["right"]["name"]),
        )
    )
    return {
        "analysis_version": ANALYSIS_VERSION,
        "skills_root": str(resolved_skills_root),
        "selected_areas": selected_areas,
        "skill_count": len(filtered_records),
        "candidate_pair_count": len(pairs),
        "pairs": pairs,
    }


def write_skill_near_dupe_report(
    project_root: Path,
    *,
    skills_root: Path,
    areas: list[str] | None = None,
    output_path: Path | None = None,
) -> dict[str, Any]:
    resolved_project_root = project_root.resolve()
    payload = analyze_skill_near_dupes(skills_root=skills_root, areas=areas)
    resolved_output = (
        output_path.resolve()
        if output_path is not None
        else resolved_project_root
        / "tmp"
        / "skill-near-dupes"
        / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        / "report.json"
    )
    write_json(resolved_output, payload)
    return {
        **payload,
        "output_path": str(resolved_output),
    }


def _select_areas(*, areas: list[str] | None, available_areas: list[str]) -> list[str]:
    if not areas:
        return available_areas

    selected_areas: list[str] = []
    unknown_areas: list[str] = []
    for area in areas:
        if area in selected_areas:
            continue
        if area not in available_areas:
            unknown_areas.append(area)
            continue
        selected_areas.append(area)
    if unknown_areas:
        raise ValueError(
            "Unknown skill area(s): "
            f"{unknown_areas}. Available areas: {available_areas or ['root']}"
        )
    return selected_areas


def _build_profile(record: DiscoveredSkillRecord) -> SkillTextProfile:
    trigger_text = _extract_trigger_text(record.skill.instructions)
    body_text = _extract_instruction_body(record.skill.instructions)
    combined_terms = Counter()
    name_terms = _tokenize(record.skill.name)
    description_terms = _tokenize(record.skill.description)
    trigger_terms = _tokenize(trigger_text)
    body_terms = _tokenize(body_text)
    for terms in (name_terms, description_terms, trigger_terms, body_terms):
        combined_terms.update(terms)
    return SkillTextProfile(
        record=record,
        name_terms=name_terms,
        description_terms=description_terms,
        trigger_terms=trigger_terms,
        body_terms=body_terms,
        combined_terms=combined_terms,
        cue_lines=_extract_disambiguation_cues(record.skill.description, trigger_text, body_text),
    )


def _build_pair(left_profile: SkillTextProfile, right_profile: SkillTextProfile) -> dict[str, Any] | None:
    left_profile, right_profile = _order_profiles(left_profile, right_profile)
    left_name = left_profile.record.skill.name.strip().lower()
    right_name = right_profile.record.skill.name.strip().lower()
    same_name = left_name == right_name
    score = _pair_score(left_profile, right_profile, same_name=same_name)
    if not same_name and score < NEAR_DUPE_THRESHOLD:
        return None

    return {
        "left": _serialize_record(left_profile.record),
        "right": _serialize_record(right_profile.record),
        "score": round(score, 3),
        "severity": "high" if same_name or score >= HIGH_SEVERITY_THRESHOLD else "medium",
        "same_name": same_name,
        "shared_terms": _shared_terms(left_profile.combined_terms, right_profile.combined_terms),
        "disambiguation_cues": _pair_disambiguation_cues(left_profile, right_profile),
    }


def _order_profiles(
    left_profile: SkillTextProfile,
    right_profile: SkillTextProfile,
) -> tuple[SkillTextProfile, SkillTextProfile]:
    left_key = (
        left_profile.record.relative_path.as_posix(),
        left_profile.record.skill.name,
    )
    right_key = (
        right_profile.record.relative_path.as_posix(),
        right_profile.record.skill.name,
    )
    if left_key <= right_key:
        return left_profile, right_profile
    return right_profile, left_profile


def _pair_score(
    left_profile: SkillTextProfile,
    right_profile: SkillTextProfile,
    *,
    same_name: bool,
) -> float:
    name_similarity = 1.0 if same_name else _cosine_similarity(
        left_profile.name_terms,
        right_profile.name_terms,
    )
    description_similarity = _cosine_similarity(
        left_profile.description_terms,
        right_profile.description_terms,
    )
    trigger_similarity = _cosine_similarity(
        left_profile.trigger_terms,
        right_profile.trigger_terms,
    )
    body_similarity = _cosine_similarity(
        left_profile.body_terms,
        right_profile.body_terms,
    )
    overall_similarity = _cosine_similarity(
        left_profile.combined_terms,
        right_profile.combined_terms,
    )
    score = (
        0.25 * name_similarity
        + 0.15 * description_similarity
        + 0.25 * trigger_similarity
        + 0.20 * body_similarity
        + 0.15 * overall_similarity
    )
    if same_name:
        score = max(score, SAME_NAME_SCORE_FLOOR)
    return min(score, 1.0)


def _serialize_record(record: DiscoveredSkillRecord) -> dict[str, str]:
    return {
        "name": record.skill.name,
        "area": record.area,
        "path": record.relative_path.as_posix(),
        "description": record.skill.description,
    }


def _shared_terms(
    left_terms: Counter[str],
    right_terms: Counter[str],
    *,
    limit: int = 8,
) -> list[str]:
    ranked = sorted(
        set(left_terms).intersection(right_terms),
        key=lambda term: (-min(left_terms[term], right_terms[term]), term),
    )
    return ranked[:limit]


def _pair_disambiguation_cues(
    left_profile: SkillTextProfile,
    right_profile: SkillTextProfile,
) -> list[str]:
    cues: list[str] = []
    for profile in (left_profile, right_profile):
        for cue in profile.cue_lines[:2]:
            formatted_cue = f"{profile.record.skill.name}: {cue}"
            if formatted_cue not in cues:
                cues.append(formatted_cue)
    return cues


def _extract_trigger_text(instructions: str) -> str:
    match = TRIGGER_SECTION_PATTERN.search(instructions)
    if match is None:
        return ""
    return str(match.group("trigger") or "").strip()


def _extract_instruction_body(instructions: str) -> str:
    match = INSTRUCTION_SECTION_PATTERN.search(instructions)
    if match is not None:
        return str(match.group("body") or "").strip()
    return instructions.strip()


def _extract_disambiguation_cues(description: str, trigger_text: str, body_text: str) -> list[str]:
    cues: list[str] = []
    source_lines = [description]
    source_lines.extend(trigger_text.splitlines())
    source_lines.extend(body_text.splitlines()[:12])
    for raw_line in source_lines:
        line = _normalize_line(raw_line)
        if not line:
            continue
        lowered = line.lower()
        if not any(hint in lowered for hint in DISAMBIGUATION_HINTS):
            continue
        if line not in cues:
            cues.append(line)
    return cues


def _normalize_line(raw_line: str) -> str:
    line = raw_line.strip()
    if not line or line.startswith("#") or line == "Instructions:" or line == "Use this skill when:":
        return ""
    line = LINE_PREFIX_PATTERN.sub("", line).strip()
    return line


def _tokenize(text: str) -> Counter[str]:
    tokens: Counter[str] = Counter()
    for match in TOKEN_PATTERN.finditer(text.lower()):
        raw_token = match.group(0).strip("-")
        if not raw_token:
            continue
        for token in _expand_token(raw_token):
            if token in STOPWORDS or len(token) < 3:
                continue
            tokens[token] += 1
    return tokens


def _expand_token(token: str) -> list[str]:
    tokens = [token]
    if "-" in token:
        tokens.extend(part for part in token.split("-") if part)
    return tokens


def _cosine_similarity(left_terms: Counter[str], right_terms: Counter[str]) -> float:
    if not left_terms or not right_terms:
        return 0.0
    shared_terms = set(left_terms).intersection(right_terms)
    if not shared_terms:
        return 0.0

    numerator = sum(left_terms[term] * right_terms[term] for term in shared_terms)
    left_norm = sum(count * count for count in left_terms.values()) ** 0.5
    right_norm = sum(count * count for count in right_terms.values()) ** 0.5
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return numerator / (left_norm * right_norm)
