from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm.skill_evals import load_skill_eval_suite
from moltfarm.skill_loader import load_skill


class SkillEvalSuiteTests(unittest.TestCase):
    def test_load_skill_eval_suite_normalizes_assertions_to_goal_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "sample-skill"
            files_dir = skill_dir / "evals" / "files"
            files_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: sample-skill\ndescription: Sample.\n---\n\nDo it.\n",
                encoding="utf-8",
            )
            (files_dir / "sample.json").write_text("{}", encoding="utf-8")
            (skill_dir / "evals" / "evals.json").write_text(
                json.dumps(
                    {
                        "skill_name": "sample-skill",
                        "evals": [
                            {
                                "id": "case-one",
                                "prompt": "Summarize the file.",
                                "expected_output": "A compact summary.",
                                "files": ["evals/files/sample.json"],
                                "assertions": ["The summary states the outcome"],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            suite = load_skill_eval_suite(load_skill(skill_dir / "SKILL.md"))

            self.assertIsNotNone(suite)
            self.assertEqual(1, len(suite.cases))
            self.assertEqual("The summary states the outcome", suite.cases[0].checks[0].text)
            self.assertEqual("goal", suite.cases[0].checks[0].category)
            self.assertEqual(1.0, suite.cases[0].checks[0].weight)

    def test_load_skill_eval_suite_validates_structured_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "sample-skill"
            files_dir = skill_dir / "evals" / "files"
            files_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: sample-skill\ndescription: Sample.\n---\n\nDo it.\n",
                encoding="utf-8",
            )
            (files_dir / "sample.json").write_text("{}", encoding="utf-8")
            (skill_dir / "evals" / "evals.json").write_text(
                json.dumps(
                    {
                        "skill_name": "sample-skill",
                        "evals": [
                            {
                                "id": "case-one",
                                "prompt": "Summarize the file.",
                                "expected_output": "A compact summary.",
                                "files": ["evals/files/sample.json"],
                                "checks": [
                                    {
                                        "text": "The summary solves the user task",
                                        "category": "goal",
                                        "weight": 3,
                                    },
                                    {
                                        "text": "The summary cites the artifact path",
                                        "category": "evidence",
                                        "weight": 2,
                                    },
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            suite = load_skill_eval_suite(load_skill(skill_dir / "SKILL.md"))

            self.assertEqual(["goal", "evidence"], [check.category for check in suite.cases[0].checks])
            self.assertEqual([3.0, 2.0], [check.weight for check in suite.cases[0].checks])

    def test_load_skill_eval_suite_rejects_invalid_check_category(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "sample-skill"
            files_dir = skill_dir / "evals" / "files"
            files_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\nname: sample-skill\ndescription: Sample.\n---\n\nDo it.\n",
                encoding="utf-8",
            )
            (files_dir / "sample.json").write_text("{}", encoding="utf-8")
            (skill_dir / "evals" / "evals.json").write_text(
                json.dumps(
                    {
                        "skill_name": "sample-skill",
                        "evals": [
                            {
                                "id": "case-one",
                                "prompt": "Summarize the file.",
                                "expected_output": "A compact summary.",
                                "files": ["evals/files/sample.json"],
                                "checks": [
                                    {
                                        "text": "Bad category",
                                        "category": "style",
                                        "weight": 1,
                                    }
                                ],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_skill_eval_suite(load_skill(skill_dir / "SKILL.md"))


if __name__ == "__main__":
    unittest.main()
