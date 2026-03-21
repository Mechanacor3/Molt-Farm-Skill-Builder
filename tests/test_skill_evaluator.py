from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm import skill_evaluator


class SkillEvaluatorTests(unittest.TestCase):
    def test_evaluate_skill_creates_workspace_artifacts(self) -> None:
        original_execute_task = skill_evaluator.execute_task
        original_load_sdk = skill_evaluator._load_sdk
        try:
            def fake_execute_task(*, project_root, agent, skills, task_input):
                del project_root, agent
                label = "with" if skills else "without"
                summary = (
                    "attempted: test\n"
                    "happened: looked at the run record.\n"
                    f"status: {'completed' if skills else 'failed'}\n"
                    "produced: wrote a compact summary.\n"
                    "gaps: none\n"
                    "next_step: none"
                )
                return "completed", {
                    "summary": summary,
                    "metrics": {
                        "duration_ms": 123 if skills else 45,
                        "usage": {
                            "requests": 1,
                            "input_tokens": 10,
                            "output_tokens": 20,
                            "total_tokens": 30 if skills else 15,
                        },
                    },
                    "trace": {
                        "response_ids": [f"resp-{label}"],
                        "request_ids": [f"req-{label}"],
                        "items": (
                            [{"type": "tool_call_item", "summary": "function_call:activate_skill:sample-skill"}]
                            if skills
                            else [{"type": "message_output_item", "summary": "ok"}]
                        ),
                    },
                }

            class FakeResult:
                def __init__(self, final_output: str):
                    self.final_output = final_output

            class FakeRunner:
                @staticmethod
                def run_sync(agent, prompt):
                    del agent, prompt
                    payload = {
                        "assertion_results": [
                            {
                                "text": "The summary includes attempted",
                                "passed": True,
                                "evidence": "Found attempted field.",
                            }
                        ],
                        "summary": {
                            "passed": 1,
                            "failed": 0,
                            "total": 1,
                            "pass_rate": 1.0,
                        },
                    }
                    return FakeResult(json.dumps(payload))

            class FakeSDK:
                Runner = FakeRunner

                class Agent:
                    def __init__(self, **kwargs):
                        self.kwargs = kwargs

                @staticmethod
                def set_tracing_disabled(value):
                    del value

            skill_evaluator.execute_task = fake_execute_task
            skill_evaluator._load_sdk = lambda project_root: FakeSDK

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                skill_dir = project_root / "skills" / "sample-skill"
                files_dir = skill_dir / "evals" / "files"
                files_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(
                    "---\nname: sample-skill\ndescription: Sample.\n---\n\nDo the thing.\n",
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
                                    "prompt": "Summarize evals/files/sample.json",
                                    "expected_output": "Structured output",
                                    "files": ["evals/files/sample.json"],
                                    "assertions": ["The summary includes attempted"],
                                    "required_skill_activations": ["sample-skill"],
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )

                result = skill_evaluator.evaluate_skill(
                    project_root,
                    skill_name="sample-skill",
                    model="gpt-5",
                )

                self.assertEqual("sample-skill", result["skill_name"])
                iteration_dir = project_root / result["iteration_dir"]
                self.assertTrue((iteration_dir / "benchmark.json").is_file())
                self.assertTrue((iteration_dir / "feedback.json").is_file())
                self.assertTrue(
                    (iteration_dir / "eval-case-one" / "with_skill" / "timing.json").is_file()
                )
                self.assertTrue(
                    (iteration_dir / "eval-case-one" / "without_skill" / "grading.json").is_file()
                )
                benchmark = json.loads((iteration_dir / "benchmark.json").read_text(encoding="utf-8"))
                self.assertIn("with_skill", benchmark["run_summary"])
                self.assertIn("without_skill", benchmark["run_summary"])
                self.assertIn("delta", benchmark["run_summary"])
                with_grading = json.loads(
                    (iteration_dir / "eval-case-one" / "with_skill" / "grading.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(2, with_grading["summary"]["total"])
        finally:
            skill_evaluator.execute_task = original_execute_task
            skill_evaluator._load_sdk = original_load_sdk

    def test_evaluate_skill_can_use_latest_snapshot_as_baseline(self) -> None:
        original_execute_task = skill_evaluator.execute_task
        original_load_sdk = skill_evaluator._load_sdk
        try:
            def fake_execute_task(*, project_root, agent, skills, task_input):
                del project_root, agent, task_input
                return "completed", {
                    "summary": "attempted: x\nhappened: y\nstatus: completed\nproduced: z\ngaps: none\nnext_step: none",
                    "metrics": {
                        "duration_ms": 10,
                        "usage": {
                            "requests": 1,
                            "input_tokens": 1,
                            "output_tokens": 1,
                            "total_tokens": 2,
                        },
                    },
                    "trace": {"response_ids": [], "request_ids": [], "items": []},
                }

            class FakeResult:
                def __init__(self, final_output: str):
                    self.final_output = final_output

            class FakeRunner:
                @staticmethod
                def run_sync(agent, prompt):
                    del agent, prompt
                    return FakeResult(
                        json.dumps(
                            {
                                "assertion_results": [],
                                "summary": {
                                    "passed": 0,
                                    "failed": 0,
                                    "total": 0,
                                    "pass_rate": 0.0,
                                },
                            }
                        )
                    )

            class FakeSDK:
                Runner = FakeRunner

                class Agent:
                    def __init__(self, **kwargs):
                        self.kwargs = kwargs

                @staticmethod
                def set_tracing_disabled(value):
                    del value

            skill_evaluator.execute_task = fake_execute_task
            skill_evaluator._load_sdk = lambda project_root: FakeSDK

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                skill_dir = project_root / "skills" / "sample-skill"
                files_dir = skill_dir / "evals" / "files"
                files_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(
                    "---\nname: sample-skill\ndescription: Sample.\n---\n\nDo the thing.\n",
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
                                    "prompt": "Summarize evals/files/sample.json",
                                    "expected_output": "Structured output",
                                    "files": ["evals/files/sample.json"],
                                    "assertions": [],
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )

                first = skill_evaluator.evaluate_skill(
                    project_root,
                    skill_name="sample-skill",
                    snapshot_current=True,
                )
                second = skill_evaluator.evaluate_skill(
                    project_root,
                    skill_name="sample-skill",
                    baseline="snapshot",
                )

                self.assertIsNotNone(first["snapshot_dir"])
                second_iteration = project_root / second["iteration_dir"]
                benchmark = json.loads((second_iteration / "benchmark.json").read_text(encoding="utf-8"))
                self.assertIn("old_skill", benchmark["run_summary"])
                self.assertEqual("old_skill", benchmark["run_summary"]["delta"]["baseline"])
        finally:
            skill_evaluator.execute_task = original_execute_task
            skill_evaluator._load_sdk = original_load_sdk

    def test_evaluate_skill_can_run_without_baseline(self) -> None:
        original_execute_task = skill_evaluator.execute_task
        original_load_sdk = skill_evaluator._load_sdk
        try:
            def fake_execute_task(*, project_root, agent, skills, task_input):
                del project_root, agent, task_input
                return "completed", {
                    "summary": "goal: x\ncurrent_evidence: y\nnext_phase: z\nuse_skills: develop-web-game\nbuild_step: a\nvalidation_step: b\nstop_after: c",
                    "metrics": {
                        "duration_ms": 10,
                        "usage": {
                            "requests": 1,
                            "input_tokens": 1,
                            "output_tokens": 1,
                            "total_tokens": 2,
                        },
                    },
                    "trace": {
                        "response_ids": [],
                        "request_ids": [],
                        "items": [
                            {
                                "type": "tool_call_item",
                                "summary": "function_call:activate_skill:sample-skill",
                            }
                        ],
                    },
                }

            class FakeResult:
                def __init__(self, final_output: str):
                    self.final_output = final_output

            class FakeRunner:
                @staticmethod
                def run_sync(agent, prompt):
                    del agent, prompt
                    return FakeResult(
                        json.dumps(
                            {
                                "assertion_results": [],
                                "summary": {
                                    "passed": 0,
                                    "failed": 0,
                                    "total": 0,
                                    "pass_rate": 0.0,
                                },
                            }
                        )
                    )

            class FakeSDK:
                Runner = FakeRunner

                class Agent:
                    def __init__(self, **kwargs):
                        self.kwargs = kwargs

                @staticmethod
                def set_tracing_disabled(value):
                    del value

            skill_evaluator.execute_task = fake_execute_task
            skill_evaluator._load_sdk = lambda project_root: FakeSDK

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                skill_dir = project_root / "skills" / "sample-skill"
                files_dir = skill_dir / "evals" / "files"
                files_dir.mkdir(parents=True)
                (skill_dir / "SKILL.md").write_text(
                    "---\nname: sample-skill\ndescription: Sample.\n---\n\nDo the thing.\n",
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
                                    "prompt": "Plan the next pass.",
                                    "expected_output": "A focused plan.",
                                    "files": ["evals/files/sample.json"],
                                    "assertions": [],
                                    "required_skill_activations": ["sample-skill"],
                                }
                            ],
                        }
                    ),
                    encoding="utf-8",
                )

                result = skill_evaluator.evaluate_skill(
                    project_root,
                    skill_name="sample-skill",
                    baseline="none",
                )

                benchmark = result["benchmark"]["run_summary"]
                self.assertIn("with_skill", benchmark)
                self.assertNotIn("without_skill", benchmark)
                self.assertNotIn("delta", benchmark)
        finally:
            skill_evaluator.execute_task = original_execute_task
            skill_evaluator._load_sdk = original_load_sdk


if __name__ == "__main__":
    unittest.main()
