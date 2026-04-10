from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm.skill_evals import load_skill_eval_suite, resolve_eval_case_files
from moltfarm.skill_loader import discover_skills, load_skill


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = PROJECT_ROOT / "skills"


class RepoSkillInventoryTests(unittest.TestCase):
    def test_new_skills_are_discoverable_and_old_wiki_name_is_absent(self) -> None:
        skills = discover_skills(SKILLS_ROOT)

        self.assertIn("molt-skill-builder-authoring", skills)
        self.assertIn("llm-wiki", skills)
        self.assertIn("llm-wiki-validator", skills)
        self.assertNotIn("raw-notes-to-interlinked-wiki", skills)

    def test_new_skill_eval_suites_resolve_all_fixture_paths(self) -> None:
        expected_case_counts = {
            "molt-skill-builder-authoring": 4,
            "llm-wiki": 4,
            "llm-wiki-validator": 2,
        }

        for skill_name, expected_cases in expected_case_counts.items():
            with self.subTest(skill=skill_name):
                skill = load_skill(SKILLS_ROOT / skill_name / "SKILL.md")
                suite = load_skill_eval_suite(skill)

                self.assertIsNotNone(suite)
                self.assertEqual(expected_cases, len(suite.cases))
                for case in suite.cases:
                    resolve_eval_case_files(skill, case)

    def test_new_skills_have_agent_metadata(self) -> None:
        for skill_name in [
            "molt-skill-builder-authoring",
            "llm-wiki",
            "llm-wiki-validator",
        ]:
            with self.subTest(skill=skill_name):
                metadata = (SKILLS_ROOT / skill_name / "agents" / "openai.yaml").read_text(
                    encoding="utf-8"
                )
                self.assertIn("display_name:", metadata)
                self.assertIn("short_description:", metadata)
                self.assertIn("default_prompt:", metadata)


if __name__ == "__main__":
    unittest.main()
