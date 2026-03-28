from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm import eval_authoring


class EvalAuthoringTests(unittest.TestCase):
    def test_create_evals_new_session_writes_analysis_and_probe_artifacts(self) -> None:
        original_execute_task = eval_authoring.execute_task
        original_load_sdk = eval_authoring._load_sdk
        try:
            eval_authoring.execute_task = _fake_execute_task
            eval_authoring._load_sdk = lambda project_root: _FakeSDK()

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                _write_eval_author_skill(project_root)
                _write_sample_skill(project_root, with_existing_evals=False)

                result = eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                )

                session_dir = project_root / result["session_dir"]
                self.assertEqual("awaiting_selection", result["phase"])
                self.assertTrue((session_dir / "session.json").is_file())
                self.assertTrue((session_dir / "analysis" / "skill-profile.json").is_file())
                self.assertTrue((session_dir / "analysis" / "probe-observations.json").is_file())
                self.assertTrue((session_dir / "analysis" / "suggested-flavors.json").is_file())
                self.assertEqual(3, len(result["suggested_flavors"]))
                self.assertTrue(
                    (
                        session_dir
                        / "probes"
                        / "probe-primary-task"
                        / "with_skill"
                        / "result.json"
                    ).is_file()
                )
                self.assertTrue(
                    (
                        session_dir
                        / "probes"
                        / "probe-primary-task"
                        / "without_skill"
                        / "trace.json"
                    ).is_file()
                )
        finally:
            eval_authoring.execute_task = original_execute_task
            eval_authoring._load_sdk = original_load_sdk

    def test_create_evals_resume_builds_draft_and_preserves_existing_cases(self) -> None:
        original_execute_task = eval_authoring.execute_task
        original_load_sdk = eval_authoring._load_sdk
        try:
            eval_authoring.execute_task = _fake_execute_task
            eval_authoring._load_sdk = lambda project_root: _FakeSDK()

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                _write_eval_author_skill(project_root)
                _write_sample_skill(project_root, with_existing_evals=True)

                first = eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                )
                second = eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                    session_id=first["session_id"],
                    answers={"selected_flavors": "core-task,evidence-discipline"},
                )

                self.assertEqual("draft_ready", second["phase"])
                draft_payload = json.loads(
                    (project_root / second["draft_evals_path"]).read_text(encoding="utf-8")
                )
                self.assertEqual("keep-me", draft_payload["evals"][0]["notes"])
                self.assertEqual("core-task-2", draft_payload["evals"][1]["id"])
                self.assertEqual(
                    ["evals/files/existing-2.json"],
                    draft_payload["evals"][1]["files"],
                )
                self.assertTrue((project_root / second["draft_preview_path"]).is_file())
                self.assertIn(
                    "skills/sample-skill/evals/workspace/create-evals/session-1/draft/files/existing-2.json",
                    second["generated_fixture_paths"],
                )
        finally:
            eval_authoring.execute_task = original_execute_task
            eval_authoring._load_sdk = original_load_sdk

    def test_create_evals_promote_writes_canonical_files_and_backup(self) -> None:
        original_execute_task = eval_authoring.execute_task
        original_load_sdk = eval_authoring._load_sdk
        try:
            eval_authoring.execute_task = _fake_execute_task
            eval_authoring._load_sdk = lambda project_root: _FakeSDK()

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                _write_eval_author_skill(project_root)
                _write_sample_skill(project_root, with_existing_evals=True)

                first = eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                )
                eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                    session_id=first["session_id"],
                    answers={"selected_flavors": "core-task"},
                )
                promoted = eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                    session_id=first["session_id"],
                    promote=True,
                )

                canonical_evals = json.loads(
                    (project_root / "skills" / "sample-skill" / "evals" / "evals.json").read_text(
                        encoding="utf-8"
                    )
                )
                self.assertEqual("promoted", promoted["phase"])
                self.assertEqual("./molt skill-builder eval-skill sample-skill", promoted["next_command"])
                self.assertEqual(2, len(canonical_evals["evals"]))
                self.assertTrue((project_root / promoted["promotion_backup_path"]).is_file())
                self.assertTrue(
                    (project_root / "skills" / "sample-skill" / "evals" / "files" / "existing-2.json").is_file()
                )
                self.assertFalse(
                    (project_root / "skills" / "sample-skill" / "evals" / "workspace" / "iteration-1").exists()
                )
        finally:
            eval_authoring.execute_task = original_execute_task
            eval_authoring._load_sdk = original_load_sdk

    def test_create_evals_rejects_unknown_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_eval_author_skill(project_root)
            _write_sample_skill(project_root, with_existing_evals=False)

            with self.assertRaises(ValueError):
                eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                    session_id="session-99",
                )

    def test_create_evals_rejects_promote_before_draft_ready(self) -> None:
        original_execute_task = eval_authoring.execute_task
        original_load_sdk = eval_authoring._load_sdk
        try:
            eval_authoring.execute_task = _fake_execute_task
            eval_authoring._load_sdk = lambda project_root: _FakeSDK()

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                _write_eval_author_skill(project_root)
                _write_sample_skill(project_root, with_existing_evals=False)

                first = eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                )

                with self.assertRaises(ValueError):
                    eval_authoring.create_evals(
                        project_root,
                        skill_name="sample-skill",
                        session_id=first["session_id"],
                        promote=True,
                    )
        finally:
            eval_authoring.execute_task = original_execute_task
            eval_authoring._load_sdk = original_load_sdk


def _write_eval_author_skill(project_root: Path) -> None:
    skill_dir = project_root / "skills" / "eval-author"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: eval-author\ndescription: Draft evals.\n---\n\nDraft evals.\n",
        encoding="utf-8",
    )


def _write_sample_skill(project_root: Path, *, with_existing_evals: bool) -> None:
    skill_dir = project_root / "skills" / "sample-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: sample-skill\ndescription: Summarize narrow local artifacts.\n---\n\nUse local artifacts.\n",
        encoding="utf-8",
    )
    files_dir = skill_dir / "evals" / "files"
    files_dir.mkdir(parents=True)
    (files_dir / "existing.json").write_text('{"result": "ok"}', encoding="utf-8")

    if not with_existing_evals:
        return

    (skill_dir / "evals" / "evals.json").write_text(
        json.dumps(
            {
                "skill_name": "sample-skill",
                "evals": [
                    {
                        "id": "core-task",
                        "prompt": "Summarize the existing artifact.",
                        "expected_output": "A concise artifact summary.",
                        "files": ["evals/files/existing.json"],
                        "checks": [
                            {
                                "text": "The summary solves the task",
                                "category": "goal",
                                "weight": 3,
                            }
                        ],
                        "notes": "keep-me",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def _fake_execute_task(*, project_root, agent, skills, task_input):
    del project_root, agent
    with_skill = bool(skills)
    prompt = task_input["task"]
    return "completed", {
        "summary": f"{'with' if with_skill else 'without'} skill: {prompt}",
        "metrics": {
            "duration_ms": 20 if with_skill else 10,
            "usage": {
                "requests": 1,
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30,
            },
        },
        "trace": {
            "response_ids": [],
            "request_ids": [],
            "items": (
                [
                    {
                        "type": "tool_call_item",
                        "summary": "function_call:activate_skill:sample-skill",
                    }
                ]
                if with_skill
                else []
            ),
        },
    }


class _FakeResult:
    def __init__(self, final_output: str):
        self.final_output = final_output


class _FakeRunner:
    @staticmethod
    def run_sync(agent, prompt):
        del prompt
        if agent.name == "eval-author-flavor-suggester":
            return _FakeResult(
                json.dumps(
                    {
                        "suggested_flavors": [
                            {
                                "id": "core-task",
                                "title": "Core Task Coverage",
                                "rationale": "Cover the main job.",
                                "recommended": True,
                                "evidence": ["Probe evidence from primary-task"],
                                "fixture_strategy": "Reuse or add one narrow fixture.",
                            },
                            {
                                "id": "evidence-discipline",
                                "title": "Evidence Discipline",
                                "rationale": "Check artifact grounding.",
                                "recommended": False,
                                "evidence": ["Probe evidence from evidence-discipline"],
                                "fixture_strategy": "Use one explicit artifact file.",
                            },
                            {
                                "id": "variation-case",
                                "title": "Variation Case",
                                "rationale": "Cover a realistic variation.",
                                "recommended": False,
                                "evidence": ["Probe evidence from next-phase"],
                                "fixture_strategy": "Keep the fixture local and small.",
                            },
                        ]
                    }
                )
            )
        if agent.name == "eval-author-suite-drafter":
            return _FakeResult(
                json.dumps(
                    {
                        "evals": [
                            {
                                "id": "core-task",
                                "prompt": "Summarize the new draft artifact.",
                                "expected_output": "A concise summary of the new artifact.",
                                "files": ["existing.json"],
                                "checks": [
                                    {
                                        "text": "The summary solves the user task",
                                        "category": "goal",
                                        "weight": 3,
                                    },
                                    {
                                        "text": "The summary cites the draft fixture",
                                        "category": "evidence",
                                        "weight": 2,
                                    },
                                ],
                            }
                        ],
                        "fixtures": [
                            {
                                "path": "evals/files/existing.json",
                                "content": '{"result": "draft"}',
                            }
                        ],
                        "preview_markdown": "# Draft\n",
                    }
                )
            )
        raise AssertionError(f"Unexpected authoring agent: {agent.name}")


class _FakeSDK:
    Runner = _FakeRunner

    class Agent:
        def __init__(self, **kwargs):
            self.name = kwargs.get("name")
            self.kwargs = kwargs

    @staticmethod
    def set_tracing_disabled(value):
        del value


if __name__ == "__main__":
    unittest.main()
