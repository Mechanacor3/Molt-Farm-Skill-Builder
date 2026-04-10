from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm.skill_loader import load_skill
from moltfarm import wiki_system_map


class WikiSystemMapTests(unittest.TestCase):
    def test_draft_and_promote_system_map_write_expected_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_runtime_stub(project_root, "packages/moltfarm/eval_authoring.py")
            _write_runtime_stub(project_root, "packages/moltfarm/runner.py")
            _write_runtime_stub(project_root, "skills/molt-skill-builder-authoring/SKILL.md")
            _write_runtime_stub(project_root, "Molt-Farm-Proxy/app/main.py")
            _write_runtime_stub(project_root, "Molt-Farm-Proxy/app/translator.py")
            _write_lessons(project_root)

            draft = wiki_system_map.draft_system_map(
                project_root,
                lesson_glob="lessons/*.md",
            )

            self.assertEqual("session-1", draft["draft_session_id"])
            self.assertTrue((project_root / draft["draft_plan_path"]).is_file())
            self.assertTrue((project_root / draft["draft_index_path"]).is_file())
            self.assertIn("wiki/drafts/session-1/pages/index.md", draft["draft_page_paths"])
            self.assertIn(
                "wiki/drafts/session-1/pages/workflows/author-skill.md",
                draft["draft_page_paths"],
            )
            self.assertFalse((project_root / "wiki" / "index.md").is_file())

            draft_index = json.loads((project_root / draft["draft_index_path"]).read_text(encoding="utf-8"))
            self.assertEqual(2, len(draft_index["entries"]))
            self.assertEqual(
                ["packages/moltfarm/eval_authoring.py", "skills/molt-skill-builder-authoring/SKILL.md"],
                draft_index["entries"][0]["supporting_paths"],
            )

            promoted = wiki_system_map.promote_system_map(project_root, session_id="session-1")
            self.assertEqual("completed", promoted["status"])
            self.assertTrue((project_root / "wiki" / "index.md").is_file())
            self.assertTrue((project_root / "wiki" / "_build" / "lesson-index.json").is_file())
            author_page = (project_root / "wiki" / "workflows" / "author-skill.md").read_text(encoding="utf-8")
            self.assertIn("Supporting lesson:", author_page)
            self.assertIn("lessons/2026-04-09-authoring.md", author_page)
            index_page = (project_root / "wiki" / "index.md").read_text(encoding="utf-8")
            self.assertIn("workflows/author-skill.md", index_page)

    def test_draft_system_map_marks_conflicting_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_runtime_stub(project_root, "Molt-Farm-Proxy/app/main.py")
            lessons_root = project_root / "lessons"
            lessons_root.mkdir(parents=True)
            (lessons_root / "2026-04-09-proxy-prefer.md").write_text(
                "# Proxy Prefer\n\n"
                "Source:\n"
                "- proxy: `Molt-Farm-Proxy/app/main.py`\n\n"
                "## Guidance\n\n"
                "- `lesson`: Use the proxy first for local model validation.\n"
                "- `evidence`: The proxy exposed the required local surface.\n"
                "- `scope`: proxy rollout strategy\n"
                "- `reuse`: Prefer the proxy path before any direct model path.\n",
                encoding="utf-8",
            )
            (lessons_root / "2026-04-09-proxy-avoid.md").write_text(
                "# Proxy Avoid\n\n"
                "Source:\n"
                "- proxy: `Molt-Farm-Proxy/app/main.py`\n\n"
                "## Guidance\n\n"
                "- `lesson`: Do not use the proxy first for local model validation.\n"
                "- `evidence`: Direct runs removed the proxy dependency.\n"
                "- `scope`: proxy rollout strategy\n"
                "- `reuse`: Avoid the proxy path until direct runs are stable.\n",
                encoding="utf-8",
            )

            draft = wiki_system_map.draft_system_map(project_root, lesson_glob="lessons/*.md")
            payload = json.loads((project_root / draft["draft_index_path"]).read_text(encoding="utf-8"))
            self.assertEqual(
                ["conflict", "conflict"],
                sorted(entry["claim_status"] for entry in payload["entries"]),
            )

    def test_promoted_index_supports_skill_lookup_before_raw_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            skill_dir = project_root / "skills" / "sample-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: sample-skill\ndescription: Sample skill.\n---\n\nUse sample skill.\n",
                encoding="utf-8",
            )
            lessons_root = project_root / "lessons"
            lessons_root.mkdir(parents=True)
            (lessons_root / "generic.md").write_text(
                "# Generic Lesson\n\n"
                "Source:\n"
                "- note: `README.md`\n\n"
                "## Guidance\n\n"
                "- `lesson`: Keep the output contract stable.\n"
                "- `evidence`: The revised flow removed ad hoc fields.\n"
                "- `scope`: structured reporting\n"
                "- `reuse`: Prefer one stable output contract.\n",
                encoding="utf-8",
            )
            promoted_root = project_root / "wiki" / "_build"
            promoted_root.mkdir(parents=True)
            (promoted_root / "lesson-index.json").write_text(
                json.dumps(
                    {
                        "entries": [
                            {
                                "source_path": "lessons/generic.md",
                                "title": "Generic Lesson: Guidance",
                                "lesson": "Keep the output contract stable.",
                                "evidence": "The revised flow removed ad hoc fields.",
                                "scope": "structured reporting",
                                "reuse": "Prefer one stable output contract.",
                                "workflow_pages": ["workflows/refine-and-rerun.md"],
                                "component_pages": ["components/skill-instructions.md"],
                                "claim_status": "stable",
                                "supporting_paths": ["skills/sample-skill/SKILL.md"],
                            }
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            skill = load_skill(skill_dir / "SKILL.md")
            matches = wiki_system_map.find_relevant_lessons(project_root, skill=skill)
            self.assertEqual(1, len(matches))
            self.assertEqual("lessons/generic.md", matches[0]["path"])
            self.assertIn("Keep the output contract stable.", matches[0]["excerpt"])


def _write_runtime_stub(project_root: Path, relative_path: str) -> None:
    path = project_root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# stub\n", encoding="utf-8")


def _write_lessons(project_root: Path) -> None:
    lessons_root = project_root / "lessons"
    lessons_root.mkdir(parents=True, exist_ok=True)
    (lessons_root / "2026-04-09-authoring.md").write_text(
        "# Authoring Lessons\n\n"
        "Source:\n"
        "- feature: `packages/moltfarm/eval_authoring.py`\n"
        "- skill: `skills/molt-skill-builder-authoring/SKILL.md`\n\n"
        "## Draft First\n\n"
        "- `lesson`: Conversational eval creation should write a reviewable draft workspace before it touches canonical files.\n"
        "- `evidence`: The draft flow writes session artifacts before any promotion step.\n"
        "- `scope`: eval authoring workflow\n"
        "- `reuse`: Keep the first pass additive and inspectable.\n",
        encoding="utf-8",
    )
    (lessons_root / "2026-04-09-local-model.md").write_text(
        "# Local Model Lessons\n\n"
        "Source:\n"
        "- runtime: `packages/moltfarm/runner.py`\n"
        "- proxy: `Molt-Farm-Proxy/app/main.py`\n"
        "- translator: `Molt-Farm-Proxy/app/translator.py`\n\n"
        "## Direct First\n\n"
        "- `lesson`: For a local-model pilot, make direct chat-completions the baseline path and treat proxy-backed Responses as a second surface.\n"
        "- `evidence`: Direct runs passed before the proxy path reached compatibility.\n"
        "- `scope`: local model integration strategy\n"
        "- `reuse`: Prove the direct local path first, then layer the proxy on top.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
