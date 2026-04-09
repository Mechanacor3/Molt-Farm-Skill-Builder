from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm import skill_evaluator


class SkillEvaluatorTests(unittest.TestCase):
    def test_align_grading_payload_recovers_paraphrased_results_by_position(self) -> None:
        checks = [
            skill_evaluator.EvalCheck(text="The answer recommends pytest parametrization", category="goal", weight=3),
            skill_evaluator.EvalCheck(text="The answer mentions input and expected pairs", category="evidence", weight=2),
        ]

        payload = {
            "assertion_results": [
                {
                    "text": "Recommend using pytest parametrize for repeated cases",
                    "passed": True,
                    "evidence": "It explicitly recommends pytest parametrize.",
                },
                {
                    "text": "Mention a single table with input/expected values",
                    "passed": True,
                    "evidence": "It describes input/expected pairs in one test.",
                },
            ]
        }

        aligned = skill_evaluator._align_grading_payload(
            checks=checks,
            payload=payload,
            mode="llm_grader",
        )

        self.assertEqual(2, aligned["summary"]["passed"])
        self.assertEqual(
            "It explicitly recommends pytest parametrize.",
            aligned["assertion_results"][0]["evidence"],
        )
        self.assertEqual(
            "It describes input/expected pairs in one test.",
            aligned["assertion_results"][1]["evidence"],
        )

    def test_align_grading_payload_prefers_exact_text_matches(self) -> None:
        checks = [
            skill_evaluator.EvalCheck(text="First exact check", category="goal", weight=1),
            skill_evaluator.EvalCheck(text="Second exact check", category="goal", weight=1),
        ]

        payload = {
            "assertion_results": [
                {
                    "text": "Second exact check",
                    "passed": False,
                    "evidence": "Second failed.",
                },
                {
                    "text": "First exact check",
                    "passed": True,
                    "evidence": "First passed.",
                },
            ]
        }

        aligned = skill_evaluator._align_grading_payload(
            checks=checks,
            payload=payload,
            mode="llm_grader",
        )

        self.assertTrue(aligned["assertion_results"][0]["passed"])
        self.assertEqual("First passed.", aligned["assertion_results"][0]["evidence"])
        self.assertFalse(aligned["assertion_results"][1]["passed"])
        self.assertEqual("Second failed.", aligned["assertion_results"][1]["evidence"])

    def test_evaluate_skill_creates_comparison_and_task_uplift_summary(self) -> None:
        original_execute_task = skill_evaluator.execute_task
        original_load_sdk = skill_evaluator._load_sdk
        try:
            def fake_execute_task(*, project_root, agent, skills, task_input, model_role=None, model_override=None):
                del project_root, agent, task_input
                del model_role, model_override
                with_skill = bool(skills)
                return "completed", {
                    "summary": (
                        "attempted: test\n"
                        "happened: used the provided artifact.\n"
                        f"status: {'completed' if with_skill else 'partial'}\n"
                        "produced: wrote a concise answer.\n"
                        "gaps: none\n"
                        "next_step: none"
                    ),
                    "metrics": {
                        "duration_ms": 120 if with_skill else 45,
                        "usage": {
                            "requests": 1,
                            "input_tokens": 10,
                            "output_tokens": 20,
                            "total_tokens": 40 if with_skill else 15,
                        },
                    },
                    "trace": {
                        "response_ids": ["resp-with" if with_skill else "resp-without"],
                        "request_ids": ["req-with" if with_skill else "req-without"],
                        "items": (
                            [{"type": "tool_call_item", "summary": "function_call:activate_skill:sample-skill"}]
                            if with_skill
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
                    del agent
                    is_baseline = "Configuration: no-skill baseline" in prompt
                    payload = {
                        "assertion_results": [
                            {
                                "text": "The answer solves the requested task",
                                "passed": not is_baseline,
                                "evidence": "It directly solves the task." if not is_baseline else "The answer does not complete the task.",
                            },
                            {
                                "text": "The answer cites the attached artifact",
                                "passed": not is_baseline,
                                "evidence": "It cites the artifact." if not is_baseline else "No concrete artifact citation.",
                            },
                            {
                                "text": "The answer keeps the required output shape",
                                "passed": True,
                                "evidence": "The requested shape is present.",
                            },
                        ],
                        "summary": {
                            "passed": 3 if not is_baseline else 1,
                            "failed": 0 if not is_baseline else 2,
                            "total": 3,
                            "pass_rate": 1.0 if not is_baseline else 0.3333,
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
            skill_evaluator._load_sdk = (
                lambda project_root, model, model_override=None: (FakeSDK, model, None)
            )

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
                                    "checks": [
                                        {
                                            "text": "The answer solves the requested task",
                                            "category": "goal",
                                            "weight": 3,
                                        },
                                        {
                                            "text": "The answer cites the attached artifact",
                                            "category": "evidence",
                                            "weight": 2,
                                        },
                                        {
                                            "text": "The answer keeps the required output shape",
                                            "category": "format",
                                            "weight": 1,
                                        },
                                    ],
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

                iteration_dir = project_root / result["iteration_dir"]
                self.assertTrue((iteration_dir / "benchmark.json").is_file())
                self.assertTrue((iteration_dir / "feedback.json").is_file())
                self.assertTrue((iteration_dir / "eval-case-one" / "comparison.json").is_file())

                benchmark = json.loads((iteration_dir / "benchmark.json").read_text(encoding="utf-8"))
                self.assertEqual(1.0, benchmark["with_skill_win_rate"])
                self.assertGreater(benchmark["task_uplift_score"], 0.0)
                self.assertTrue(benchmark["promotion_signal"]["successful"])
                self.assertIn("goal", benchmark["category_scores"]["with_skill"])

                comparison = json.loads(
                    (iteration_dir / "eval-case-one" / "comparison.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual("with_skill", comparison["winner"])
                self.assertGreater(comparison["goal_score_delta"], 0.0)
                self.assertGreater(comparison["evidence_score_delta"], 0.0)

                with_grading = json.loads(
                    (iteration_dir / "eval-case-one" / "with_skill" / "grading.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual(4, with_grading["summary"]["total"])
                self.assertIn("trigger", with_grading["category_scores"])
        finally:
            skill_evaluator.execute_task = original_execute_task
            skill_evaluator._load_sdk = original_load_sdk

    def test_format_only_gain_does_not_count_as_task_uplift(self) -> None:
        comparison = skill_evaluator._build_case_comparison(
            with_skill={
                "category_scores": {
                    "goal": {"score": 0.0},
                    "evidence": {"score": 0.0},
                    "format": {"score": 1.0},
                },
                "timing": {"duration_ms": 10, "total_tokens": 20, "requests": 1},
            },
            baseline={
                "category_scores": {
                    "goal": {"score": 0.0},
                    "evidence": {"score": 0.0},
                    "format": {"score": 0.0},
                },
                "timing": {"duration_ms": 5, "total_tokens": 10, "requests": 1},
            },
            baseline_label="without_skill",
        )

        self.assertEqual("tie", comparison["winner"])
        self.assertEqual(0.0, comparison["task_uplift_score"])
        self.assertEqual(1.0, comparison["format_score_delta"])

    def test_evaluate_skill_can_use_latest_snapshot_as_baseline(self) -> None:
        original_execute_task = skill_evaluator.execute_task
        original_load_sdk = skill_evaluator._load_sdk
        try:
            def fake_execute_task(*, project_root, agent, skills, task_input, model_role=None, model_override=None):
                del project_root, agent, skills, task_input
                del model_role, model_override
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
                                "assertion_results": [
                                    {
                                        "text": "The answer solves the requested task",
                                        "passed": True,
                                        "evidence": "Solved.",
                                    }
                                ],
                                "summary": {
                                    "passed": 1,
                                    "failed": 0,
                                    "total": 1,
                                    "pass_rate": 1.0,
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
            skill_evaluator._load_sdk = (
                lambda project_root, model, model_override=None: (FakeSDK, model, None)
            )

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
                                    "checks": [
                                        {
                                            "text": "The answer solves the requested task",
                                            "category": "goal",
                                            "weight": 1,
                                        }
                                    ],
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
                self.assertEqual("old_skill", benchmark["comparison_summary"]["baseline_label"])
        finally:
            skill_evaluator.execute_task = original_execute_task
            skill_evaluator._load_sdk = original_load_sdk

    def test_evaluate_skill_can_run_without_baseline(self) -> None:
        original_execute_task = skill_evaluator.execute_task
        original_load_sdk = skill_evaluator._load_sdk
        try:
            def fake_execute_task(*, project_root, agent, skills, task_input, model_role=None, model_override=None):
                del project_root, agent, skills, task_input
                del model_role, model_override
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
                                "assertion_results": [
                                    {
                                        "text": "The plan is focused",
                                        "passed": True,
                                        "evidence": "Focused.",
                                    }
                                ],
                                "summary": {
                                    "passed": 1,
                                    "failed": 0,
                                    "total": 1,
                                    "pass_rate": 1.0,
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
            skill_evaluator._load_sdk = (
                lambda project_root, model, model_override=None: (FakeSDK, model, None)
            )

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
                                    "checks": [
                                        {
                                            "text": "The plan is focused",
                                            "category": "goal",
                                            "weight": 1,
                                        }
                                    ],
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

                benchmark = result["benchmark"]
                self.assertIn("with_skill", benchmark["run_summary"])
                self.assertNotIn("without_skill", benchmark["run_summary"])
                self.assertNotIn("delta", benchmark["run_summary"])
                self.assertNotIn("comparison_summary", benchmark)
                self.assertNotIn("task_uplift_score", benchmark)
        finally:
            skill_evaluator.execute_task = original_execute_task
            skill_evaluator._load_sdk = original_load_sdk

    def test_evaluate_skill_splits_subject_and_grader_models(self) -> None:
        original_execute_task = skill_evaluator.execute_task
        original_load_sdk = skill_evaluator._load_sdk
        captured: dict[str, Any] = {}
        try:
            def fake_execute_task(*, project_root, agent, skills, task_input, model_role=None, model_override=None):
                del project_root, agent, task_input
                captured.setdefault("subject_calls", []).append(
                    {
                        "skills": [skill.name for skill in skills],
                        "model_role": model_role,
                        "model_override": model_override,
                    }
                )
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
                    del prompt
                    captured.setdefault("grader_models", []).append(agent.kwargs["model"])
                    return FakeResult(
                        json.dumps(
                            {
                                "assertion_results": [
                                    {
                                        "text": "The plan is focused",
                                        "passed": True,
                                        "evidence": "Focused.",
                                    }
                                ],
                                "summary": {
                                    "passed": 1,
                                    "failed": 0,
                                    "total": 1,
                                    "pass_rate": 1.0,
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

            def fake_load_sdk(project_root, *, model, model_override=None):
                del project_root
                captured.setdefault("grader_requests", []).append(
                    {"model": model, "model_override": model_override}
                )
                return FakeSDK, f"sdk:{model}", None

            skill_evaluator.execute_task = fake_execute_task
            skill_evaluator._load_sdk = fake_load_sdk

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
                                    "checks": [
                                        {
                                            "text": "The plan is focused",
                                            "category": "goal",
                                            "weight": 1,
                                        }
                                    ],
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
                    model="gemma-4-e4b",
                    grader_model="gpt-5.4-mini",
                )

            self.assertEqual("gpt-5.4-mini", result["grader_model"])
            self.assertEqual(
                {
                    "skills": ["sample-skill"],
                    "model_role": "subject",
                    "model_override": "gemma-4-e4b",
                },
                captured["subject_calls"][0],
            )
            self.assertEqual(
                {"model": "gpt-5.4-mini", "model_override": "gpt-5.4-mini"},
                captured["grader_requests"][0],
            )
            self.assertEqual("sdk:gpt-5.4-mini", captured["grader_models"][0])
        finally:
            skill_evaluator.execute_task = original_execute_task
            skill_evaluator._load_sdk = original_load_sdk


if __name__ == "__main__":
    unittest.main()
