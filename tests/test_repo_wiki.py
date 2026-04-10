from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class RepoWikiTests(unittest.TestCase):
    def test_canonical_wiki_surface_exists(self) -> None:
        expected_paths = [
            PROJECT_ROOT / "wiki" / "index.md",
            PROJECT_ROOT / "wiki" / "workflows" / "author-skill.md",
            PROJECT_ROOT / "wiki" / "workflows" / "local-model-pilot.md",
            PROJECT_ROOT / "wiki" / "_build" / "lesson-index.json",
        ]
        for path in expected_paths:
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), f"Missing wiki artifact: {path}")

    def test_promoted_lesson_index_has_mapped_entries(self) -> None:
        payload = json.loads((PROJECT_ROOT / "wiki" / "_build" / "lesson-index.json").read_text(encoding="utf-8"))
        entries = payload.get("entries") or []
        self.assertTrue(entries)
        first = entries[0]
        self.assertIn("source_path", first)
        self.assertIn("workflow_pages", first)
        self.assertIn("component_pages", first)
        self.assertIn("supporting_paths", first)

    def test_local_model_workflow_page_cites_supporting_lessons(self) -> None:
        page = (PROJECT_ROOT / "wiki" / "workflows" / "local-model-pilot.md").read_text(encoding="utf-8")
        self.assertIn("Supporting lesson:", page)
        self.assertIn("lessons/2026-04-09-local-gemma-pure-local-pilot.md", page)


if __name__ == "__main__":
    unittest.main()
