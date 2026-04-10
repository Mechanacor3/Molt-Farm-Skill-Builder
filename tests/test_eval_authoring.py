from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

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

    def test_create_evals_rejects_unknown_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(ValueError):
                eval_authoring.create_evals(Path(temp_dir), skill_name="missing-skill")

    def test_create_evals_requires_session_for_answers_and_promotion(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_eval_author_skill(project_root)
            _write_sample_skill(project_root, with_existing_evals=False)

            with self.assertRaises(ValueError):
                eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                    answers={"selected_flavors": "core-task"},
                )

            with self.assertRaises(ValueError):
                eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                    promote=True,
                )

    def test_create_evals_rejects_session_owned_by_another_skill(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_eval_author_skill(project_root)
            _write_sample_skill(project_root, with_existing_evals=False, name="sample-skill")
            _write_sample_skill(project_root, with_existing_evals=False, name="other-skill")
            session_dir = (
                project_root
                / "skills"
                / "other-skill"
                / "evals"
                / "workspace"
                / "create-evals"
                / "session-1"
            )
            session_dir.mkdir(parents=True)
            (session_dir / "session.json").write_text(
                json.dumps(
                    {
                        "session_id": "session-1",
                        "skill_name": "sample-skill",
                        "phase": "awaiting_selection",
                        "status": "awaiting_input",
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                eval_authoring.create_evals(
                    project_root,
                    skill_name="other-skill",
                    session_id="session-1",
                )

    def test_create_evals_promoted_session_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_eval_author_skill(project_root)
            _write_sample_skill(project_root, with_existing_evals=False)
            session_dir = (
                project_root
                / "skills"
                / "sample-skill"
                / "evals"
                / "workspace"
                / "create-evals"
                / "session-1"
            )
            session_dir.mkdir(parents=True)
            (session_dir / "session.json").write_text(
                json.dumps(
                    {
                        "session_id": "session-1",
                        "skill_name": "sample-skill",
                        "phase": "promoted",
                        "status": "completed",
                        "selected_flavors": [],
                        "author_notes": "",
                        "skill_profile_path": None,
                        "probe_summary_path": None,
                        "suggested_flavors_path": None,
                        "draft_evals_path": None,
                        "draft_preview_path": None,
                        "draft_fixture_dir": None,
                        "promotion_backup_path": None,
                        "promoted_evals_path": "skills/sample-skill/evals/evals.json",
                        "generated_case_ids": [],
                        "generated_fixture_paths": [],
                        "copied_fixture_paths": [],
                    }
                ),
                encoding="utf-8",
            )

            resumed = eval_authoring.create_evals(
                project_root,
                skill_name="sample-skill",
                session_id="session-1",
            )

            self.assertEqual("promoted", resumed["phase"])
            self.assertEqual("./molt skill-builder eval-skill sample-skill", resumed["next_command"])

            with self.assertRaises(ValueError):
                eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                    session_id="session-1",
                    answers={"author_notes": "too late"},
                )

            with self.assertRaises(ValueError):
                eval_authoring.create_evals(
                    project_root,
                    skill_name="sample-skill",
                    session_id="session-1",
                    promote=True,
                )

    def test_create_evals_rejects_unknown_selected_flavors(self) -> None:
        original_execute_task = eval_authoring.execute_task
        original_load_sdk = eval_authoring._load_sdk
        try:
            eval_authoring.execute_task = _fake_execute_task
            eval_authoring._load_sdk = lambda project_root: _FakeSDK()

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                _write_eval_author_skill(project_root)
                _write_sample_skill(project_root, with_existing_evals=False)

                first = eval_authoring.create_evals(project_root, skill_name="sample-skill")

                with self.assertRaises(ValueError):
                    eval_authoring.create_evals(
                        project_root,
                        skill_name="sample-skill",
                        session_id=first["session_id"],
                        answers={"selected_flavors": "unknown-flavor"},
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


class EvalAuthoringHelperTests(unittest.TestCase):
    def test_promote_draft_requires_paths_and_rejects_fixture_conflicts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_sample_skill(project_root, with_existing_evals=True)
            skill = _load_skill(project_root)
            session_dir = project_root / "session"
            session_dir.mkdir()

            with self.assertRaises(ValueError):
                eval_authoring._promote_draft(
                    project_root=project_root,
                    skill=skill,
                    session={"draft_fixture_dir": "draft/files"},
                    session_dir=session_dir,
                )

            draft_dir = project_root / "draft"
            draft_dir.mkdir()
            draft_evals_path = draft_dir / "evals.json"
            draft_evals_path.write_text(
                json.dumps({"skill_name": "sample-skill", "evals": []}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                eval_authoring._promote_draft(
                    project_root=project_root,
                    skill=skill,
                    session={"draft_evals_path": "draft/evals.json"},
                    session_dir=session_dir,
                )

            draft_files_dir = draft_dir / "files"
            draft_files_dir.mkdir()
            (draft_files_dir / "existing.json").write_text('{"result": "conflict"}', encoding="utf-8")
            with self.assertRaises(ValueError):
                eval_authoring._promote_draft(
                    project_root=project_root,
                    skill=skill,
                    session={
                        "draft_evals_path": "draft/evals.json",
                        "draft_fixture_dir": "draft/files",
                    },
                    session_dir=session_dir,
                )

    def test_normalize_suggested_flavors_backfills_defaults_and_unique_ids(self) -> None:
        normalized = eval_authoring._normalize_suggested_flavors(
            payload={
                "suggested_flavors": [
                    "skip-me",
                    {
                        "id": "Core Task",
                        "title": "",
                        "rationale": "",
                        "recommended": False,
                        "evidence": "Probe line",
                        "fixture_strategy": "",
                    },
                    {"id": "Core Task"},
                ]
            },
            existing_payload={"evals": []},
            probe_payload={"probes": [{"probe_id": "probe-a"}]},
        )

        self.assertEqual(3, len(normalized))
        self.assertEqual("core-task", normalized[0]["id"])
        self.assertEqual("Core Task", normalized[0]["title"])
        self.assertEqual(["Probe line"], normalized[0]["evidence"])
        self.assertEqual("core-task-2", normalized[1]["id"])
        self.assertEqual("evidence-discipline", normalized[2]["id"])
        self.assertTrue(any(flavor["recommended"] for flavor in normalized))

    def test_normalize_case_checks_files_and_fixtures_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_sample_skill(project_root, with_existing_evals=True)
            skill = _load_skill(project_root)

            fixtures, aliases = eval_authoring._normalize_fixtures(
                skill=skill,
                raw_fixtures=[
                    {"path": "fixtures\\draft.exe", "content": "draft"},
                    {"path": "fixtures/draft.exe", "content": "second"},
                    {"path": "blank.txt", "content": "   "},
                    "not-a-fixture",
                ],
            )
            self.assertEqual(
                ["evals/files/draft.md", "evals/files/draft-2.md"],
                [fixture["path"] for fixture in fixtures],
            )
            self.assertEqual("evals/files/draft.md", aliases["fixtures/draft.exe"])
            self.assertEqual("evals/files/draft-2.md", aliases["draft.exe"])

            normalized_files = eval_authoring._normalize_case_files(
                skill=skill,
                raw_files=[
                    "fixtures/draft.exe",
                    "draft.exe",
                    "evals/files/existing.json",
                    "existing.json",
                    "missing.json",
                ],
                fixture_aliases=aliases,
            )
            self.assertEqual(
                ["evals/files/draft.md", "evals/files/draft-2.md", "evals/files/existing.json"],
                normalized_files,
            )

            normalized_checks = eval_authoring._normalize_case_checks(
                [
                    " keep me ",
                    {"text": "bad category", "category": "style", "weight": "oops"},
                    {"text": "", "category": "goal"},
                    123,
                ],
                files=normalized_files,
            )
            self.assertEqual("keep me", normalized_checks[0]["text"])
            self.assertEqual("goal", normalized_checks[1]["category"])
            self.assertEqual(1.0, normalized_checks[1]["weight"])

            fallback_checks = eval_authoring._normalize_case_checks([], files=normalized_files)
            self.assertEqual(["goal", "evidence", "format"], [check["category"] for check in fallback_checks])

    def test_normalize_draft_payload_generates_cases_and_uses_fallbacks(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_sample_skill(project_root, with_existing_evals=True)
            skill = _load_skill(project_root)
            existing_payload = eval_authoring._read_json(skill.path / "evals" / "evals.json")
            session = {"session_id": "session-1", "selected_flavors": ["core-task"], "author_notes": ""}
            suggested_flavors = [{"id": "core-task", "title": "Core Task"}]

            normalized = eval_authoring._normalize_draft_payload(
                skill=skill,
                session=session,
                existing_payload=existing_payload,
                selected_flavors=["core-task"],
                suggested_flavors=suggested_flavors,
                payload={
                    "evals": [
                        None,
                        {"id": "core-task", "prompt": "", "expected_output": "skip"},
                        {
                            "id": "core-task",
                            "prompt": "Summarize the artifact.",
                            "expected_output": "A concise summary.",
                            "files": ["existing.json"],
                            "checks": ["The answer solves the task"],
                            "required_skill_activations": ["", "sample-skill"],
                        },
                    ],
                    "fixtures": [{"path": "notes.txt", "content": "fixture"}],
                },
            )

            self.assertEqual("core-task-2", normalized["generated_cases"][0]["id"])
            self.assertEqual(["sample-skill"], normalized["generated_cases"][0]["required_skill_activations"])
            self.assertEqual(["evals/files/existing.json"], normalized["generated_cases"][0]["files"])
            self.assertEqual(["evals/files/notes.txt"], [fixture["path"] for fixture in normalized["generated_fixtures"]])

            fallback = eval_authoring._normalize_draft_payload(
                skill=skill,
                session=session,
                existing_payload=existing_payload,
                selected_flavors=["core-task"],
                suggested_flavors=suggested_flavors,
                payload={"evals": [], "fixtures": []},
            )
            self.assertEqual("core-task-2", fallback["generated_cases"][0]["id"])
            self.assertIn("Generated fixtures: 0", fallback["preview_markdown"])

    def test_payload_coercion_and_json_parsing_helpers(self) -> None:
        self.assertEqual({"value": 1}, eval_authoring._parse_json_payload({"value": 1}))
        self.assertEqual({"value": 1}, eval_authoring._parse_json_payload("prefix {\"value\": 1} suffix"))
        self.assertEqual([1, 2], eval_authoring._parse_json_payload("prefix [1, 2] suffix"))
        with self.assertRaises(ValueError):
            eval_authoring._parse_json_payload("not json")

        suggested_payload = eval_authoring.SuggestedFlavorPayload(
            suggested_flavors=[
                eval_authoring.SuggestedFlavor(
                    id="core-task",
                    title="Core Task",
                    rationale="Why",
                    fixture_strategy="Reuse",
                )
            ]
        )
        self.assertEqual(
            ["core-task"],
            [
                item["id"]
                for item in eval_authoring._coerce_suggested_flavor_payload(suggested_payload)["suggested_flavors"]
            ],
        )
        self.assertEqual(
            ["json-list"],
            [
                item["id"]
                for item in eval_authoring._coerce_suggested_flavor_payload(
                    '[{"id":"json-list","title":"JSON List","rationale":"Why","fixture_strategy":"Reuse"}]'
                )["suggested_flavors"]
            ],
        )
        self.assertEqual(
            [{"id": "incomplete"}],
            eval_authoring._coerce_suggested_flavor_payload({"suggested_flavors": [{"id": "incomplete"}]})[
                "suggested_flavors"
            ],
        )

        draft_payload = eval_authoring.DraftSuitePayload(
            evals=[eval_authoring.DraftEvalCase(id="case-one", prompt="Prompt", expected_output="Output")],
        )
        self.assertEqual(
            ["case-one"],
            [item["id"] for item in eval_authoring._coerce_draft_payload(draft_payload)["evals"]],
        )
        self.assertEqual(
            {"evals": [], "fixtures": [], "preview_markdown": ""},
            eval_authoring._coerce_draft_payload("[]"),
        )
        coerced_invalid = eval_authoring._coerce_draft_payload({"evals": [{"id": "case-one"}]})
        self.assertEqual([{"id": "case-one"}], coerced_invalid["evals"])
        self.assertEqual([], coerced_invalid["fixtures"])
        self.assertEqual("", coerced_invalid["preview_markdown"])

    def test_find_lessons_iteration_artifact_and_sdk_helpers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_eval_author_skill(project_root)
            _write_sample_skill(project_root, with_existing_evals=False)
            skill = _load_skill(project_root)

            lessons_root = project_root / "lessons"
            lessons_root.mkdir()
            (lessons_root / "match.md").write_text("sample-skill needs narrower tests\n", encoding="utf-8")
            (lessons_root / "miss.md").write_text("nothing relevant\n", encoding="utf-8")
            lessons = eval_authoring._find_relevant_lessons(project_root=project_root, skill=skill)
            self.assertEqual(1, len(lessons))
            self.assertEqual("lessons/match.md", lessons[0]["path"])

            self.assertIsNone(eval_authoring._find_latest_iteration_dir(skill))
            workspace_root = skill.path / "evals" / "workspace"
            (workspace_root / "iteration-1").mkdir(parents=True)
            latest_iteration = workspace_root / "iteration-3"
            latest_iteration.mkdir(parents=True)
            for index in range(4):
                (latest_iteration / f"artifact-{index}.json").write_text('{"ok": true}', encoding="utf-8")

            self.assertEqual(latest_iteration, eval_authoring._find_latest_iteration_dir(skill))
            self.assertEqual([], eval_authoring._read_iteration_artifacts(project_root=project_root, iteration_dir=None, pattern="*.json"))
            artifacts = eval_authoring._read_iteration_artifacts(
                project_root=project_root,
                iteration_dir=latest_iteration,
                pattern="*.json",
            )
            self.assertEqual(3, len(artifacts))

            created = eval_authoring._create_session_dir(skill)
            self.assertEqual("session-1", created.name)
            self.assertEqual("session-2", eval_authoring._create_session_dir(skill).name)

            loader_calls: list[tuple[Path, bool]] = []

            def fake_loader(path, override):
                loader_calls.append((path, override))

            fake_sdk = SimpleNamespace(set_tracing_disabled=mock.Mock())
            with (
                mock.patch.object(eval_authoring.runner, "_load_dotenv", return_value=fake_loader),
                mock.patch.object(eval_authoring.runner, "_import_openai_agents_sdk", return_value=fake_sdk),
            ):
                loaded_sdk = eval_authoring._load_sdk(project_root)

            self.assertIs(fake_sdk, loaded_sdk)
            self.assertEqual([(project_root / ".env", False)], loader_calls)
            fake_sdk.set_tracing_disabled.assert_called_once_with(True)
            self.assertEqual("eval-author", eval_authoring._load_eval_author_skill(project_root).name)

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_sample_skill(project_root, with_existing_evals=False)
            with self.assertRaises(ValueError):
                eval_authoring._load_eval_author_skill(project_root)

    def test_find_relevant_lessons_prefers_promoted_system_map_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_eval_author_skill(project_root)
            _write_sample_skill(project_root, with_existing_evals=False)
            skill = _load_skill(project_root)

            lessons_root = project_root / "lessons"
            lessons_root.mkdir(exist_ok=True)
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
                '{\n'
                '  "entries": [\n'
                '    {\n'
                '      "source_path": "lessons/generic.md",\n'
                '      "title": "Generic Lesson: Guidance",\n'
                '      "lesson": "Keep the output contract stable.",\n'
                '      "evidence": "The revised flow removed ad hoc fields.",\n'
                '      "scope": "structured reporting",\n'
                '      "reuse": "Prefer one stable output contract.",\n'
                '      "workflow_pages": ["workflows/refine-and-rerun.md"],\n'
                '      "component_pages": ["components/skill-instructions.md"],\n'
                '      "claim_status": "stable",\n'
                '      "supporting_paths": ["skills/sample-skill/SKILL.md"]\n'
                "    }\n"
                "  ]\n"
                "}\n",
                encoding="utf-8",
            )

            lessons = eval_authoring._find_relevant_lessons(project_root=project_root, skill=skill)
            self.assertEqual([{"path": "lessons/generic.md", "excerpt": lessons[0]["excerpt"]}], lessons)
            self.assertIn("Keep the output contract stable.", lessons[0]["excerpt"])


def _write_eval_author_skill(project_root: Path) -> None:
    skill_dir = project_root / "skills" / "eval-author"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: eval-author\ndescription: Draft evals.\n---\n\nDraft evals.\n",
        encoding="utf-8",
    )


def _write_sample_skill(project_root: Path, *, with_existing_evals: bool, name: str = "sample-skill") -> None:
    skill_dir = project_root / "skills" / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Summarize narrow local artifacts.\n---\n\nUse local artifacts.\n",
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


def _load_skill(project_root: Path, *, name: str = "sample-skill"):
    return eval_authoring.discover_skills(project_root / "skills")[name]


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
