from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm.models import SkillEvalCase
from moltfarm.skill_evals import (
    load_skill_eval_suite,
    next_iteration_dir,
    resolve_eval_case_files,
    snapshot_skill,
)
from moltfarm.skill_loader import load_skill


class SkillEvalSuiteTests(unittest.TestCase):
    def test_load_skill_eval_suite_returns_none_without_evals_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = _write_skill(Path(temp_dir))

            suite = load_skill_eval_suite(load_skill(skill_dir / "SKILL.md"))

            self.assertIsNone(suite)

    def test_load_skill_eval_suite_rejects_invalid_eval_payload_shapes(self) -> None:
        invalid_payloads = [
            ({"skill_name": "sample-skill", "evals": {"case": 1}}, "must be a list"),
            (
                {"skill_name": "sample-skill", "evals": ["not-a-case"]},
                "each case must be an object",
            ),
            (
                {
                    "skill_name": "sample-skill",
                    "evals": [{"id": "case-one", "expected_output": "A compact summary."}],
                },
                "prompt and expected_output are required",
            ),
        ]

        for payload, message in invalid_payloads:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as temp_dir:
                skill_dir = _write_skill(Path(temp_dir))
                _write_evals(skill_dir, payload)

                with self.assertRaises(ValueError) as raised:
                    load_skill_eval_suite(load_skill(skill_dir / "SKILL.md"))

                self.assertIn(message, str(raised.exception))

    def test_load_skill_eval_suite_normalizes_assertions_to_goal_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = _write_skill(Path(temp_dir))
            _write_evals(
                skill_dir,
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
                },
            )

            suite = load_skill_eval_suite(load_skill(skill_dir / "SKILL.md"))

            self.assertIsNotNone(suite)
            self.assertEqual(1, len(suite.cases))
            self.assertEqual("The summary states the outcome", suite.cases[0].checks[0].text)
            self.assertEqual("goal", suite.cases[0].checks[0].category)
            self.assertEqual(1.0, suite.cases[0].checks[0].weight)

    def test_load_skill_eval_suite_validates_structured_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = _write_skill(Path(temp_dir))
            _write_evals(
                skill_dir,
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
                },
            )

            suite = load_skill_eval_suite(load_skill(skill_dir / "SKILL.md"))

            self.assertEqual(["goal", "evidence"], [check.category for check in suite.cases[0].checks])
            self.assertEqual([3.0, 2.0], [check.weight for check in suite.cases[0].checks])

    def test_load_skill_eval_suite_rejects_invalid_check_payloads(self) -> None:
        invalid_cases = [
            ([{"text": "ok", "category": "style", "weight": 1}], "must be one of"),
            ("not-a-list", "'checks' must be a list"),
            ([123], "each check must be an object"),
            ([{"text": "Bad weight", "category": "goal", "weight": "oops"}], "'weight' must be numeric"),
            ([{"text": "", "category": "goal", "weight": 1}], "'text' is required"),
            ([{"text": "Bad weight", "category": "goal", "weight": -1}], "'weight' must be positive"),
        ]

        for checks, message in invalid_cases:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as temp_dir:
                skill_dir = _write_skill(Path(temp_dir))
                _write_evals(
                    skill_dir,
                    {
                        "skill_name": "sample-skill",
                        "evals": [
                            {
                                "id": "case-one",
                                "prompt": "Summarize the file.",
                                "expected_output": "A compact summary.",
                                "files": ["evals/files/sample.json"],
                                "checks": checks,
                            }
                        ],
                    },
                )

                with self.assertRaises(ValueError) as raised:
                    load_skill_eval_suite(load_skill(skill_dir / "SKILL.md"))

                self.assertIn(message, str(raised.exception))

    def test_resolve_eval_case_files_rejects_missing_and_escaped_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = _write_skill(Path(temp_dir))
            skill = load_skill(skill_dir / "SKILL.md")

            with self.assertRaises(ValueError):
                resolve_eval_case_files(
                    skill,
                    SkillEvalCase(
                        case_id="escape",
                        prompt="x",
                        expected_output="y",
                        files=[Path("../outside.json")],
                    ),
                )

            with self.assertRaises(FileNotFoundError):
                resolve_eval_case_files(
                    skill,
                    SkillEvalCase(
                        case_id="missing",
                        prompt="x",
                        expected_output="y",
                        files=[Path("evals/files/missing.json")],
                    ),
                )

    def test_next_iteration_dir_increments_existing_iterations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = _write_skill(Path(temp_dir))
            skill = load_skill(skill_dir / "SKILL.md")
            workspace = skill_dir / "evals" / "workspace"
            (workspace / "iteration-1").mkdir(parents=True)
            (workspace / "iteration-3").mkdir(parents=True)
            (workspace / "notes").mkdir(parents=True)

            iteration_dir = next_iteration_dir(skill)

            self.assertEqual("iteration-4", iteration_dir.name)
            self.assertTrue(iteration_dir.is_dir())

    def test_snapshot_skill_overwrites_existing_snapshot_and_ignores_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            skill_dir = _write_skill(project_root)
            (skill_dir / "notes.md").write_text("fresh\n", encoding="utf-8")
            (skill_dir / "workspace" / "cache.json").parent.mkdir(parents=True)
            (skill_dir / "workspace" / "cache.json").write_text("scratch\n", encoding="utf-8")
            skill = load_skill(skill_dir / "SKILL.md")

            destination_root = project_root / "snapshots"
            existing_snapshot = destination_root / "skill-snapshot" / skill.name
            existing_snapshot.mkdir(parents=True)
            (existing_snapshot / "stale.txt").write_text("old\n", encoding="utf-8")

            snapshot_dir = snapshot_skill(skill, destination_root)

            self.assertEqual(existing_snapshot, snapshot_dir)
            self.assertFalse((snapshot_dir / "stale.txt").exists())
            self.assertEqual("fresh\n", (snapshot_dir / "notes.md").read_text(encoding="utf-8"))
            self.assertFalse((snapshot_dir / "workspace").exists())


def _write_skill(project_root: Path, *, name: str = "sample-skill") -> Path:
    skill_dir = project_root / name
    files_dir = skill_dir / "evals" / "files"
    files_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Sample.\n---\n\nDo it.\n",
        encoding="utf-8",
    )
    (files_dir / "sample.json").write_text("{}", encoding="utf-8")
    return skill_dir


def _write_evals(skill_dir: Path, payload: dict[str, object]) -> None:
    (skill_dir / "evals" / "evals.json").write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
