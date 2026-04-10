from __future__ import annotations

import io
import json
import runpy
import sys
import unittest
import warnings
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm import cli
from moltfarm.cli import build_parser


class CliParserTests(unittest.TestCase):
    def test_skill_builder_run_command_parses(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            ["skill-builder", "run", "manual-triage", "--input", "target=."]
        )

        self.assertEqual("skill-builder", args.command)
        self.assertEqual("run", args.skill_builder_command)
        self.assertEqual("manual-triage", args.operation)
        self.assertEqual(["target=."], args.input)

    def test_skill_builder_eval_skill_command_parses(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "skill-builder",
                "eval-skill",
                "run-summarizer",
                "--baseline",
                "snapshot",
                "--snapshot-current",
            ]
        )

        self.assertEqual("skill-builder", args.command)
        self.assertEqual("eval-skill", args.skill_builder_command)
        self.assertEqual("run-summarizer", args.skill)
        self.assertEqual("snapshot", args.baseline)
        self.assertTrue(args.snapshot_current)
        self.assertIsNone(args.model)
        self.assertIsNone(args.grader_model)

    def test_skill_builder_eval_skill_allows_no_baseline(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "skill-builder",
                "eval-skill",
                "develop-web-game",
                "--baseline",
                "none",
                "--model",
                "gpt-5.4-nano",
            ]
        )

        self.assertEqual("none", args.baseline)
        self.assertEqual("gpt-5.4-nano", args.model)
        self.assertIsNone(args.grader_model)

    def test_skill_builder_eval_skill_accepts_grader_model_override(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "skill-builder",
                "eval-skill",
                "run-summarizer",
                "--model",
                "gemma-4-e4b",
                "--grader-model",
                "gpt-5.4-mini",
            ]
        )

        self.assertEqual("gemma-4-e4b", args.model)
        self.assertEqual("gpt-5.4-mini", args.grader_model)

    def test_skill_builder_create_evals_command_parses(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "skill-builder",
                "create-evals",
                "run-summarizer",
                "--session",
                "session-2",
                "--answer",
                "selected_flavors=core-task,evidence-discipline",
                "--answer",
                "author_notes=prefer file-backed cases",
                "--promote",
                "--model",
                "gpt-5.4",
            ]
        )

        self.assertEqual("skill-builder", args.command)
        self.assertEqual("create-evals", args.skill_builder_command)
        self.assertEqual("run-summarizer", args.skill)
        self.assertEqual("session-2", args.session)
        self.assertEqual(
            [
                "selected_flavors=core-task,evidence-discipline",
                "author_notes=prefer file-backed cases",
            ],
            args.answer,
        )
        self.assertTrue(args.promote)
        self.assertEqual("gpt-5.4", args.model)

    def test_skill_builder_promote_system_map_command_parses(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "skill-builder",
                "promote-system-map",
                "--session",
                "session-2",
            ]
        )

        self.assertEqual("skill-builder", args.command)
        self.assertEqual("promote-system-map", args.skill_builder_command)
        self.assertEqual("session-2", args.session)

    def test_skill_builder_experimental_probe_codex_trigger_parses(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "skill-builder",
                "experimental",
                "probe-codex-trigger",
                "develop-web-game",
                "--with-skill",
                "game-bootstrap",
                "--model",
                "gpt-5.4",
            ]
        )

        self.assertEqual("skill-builder", args.command)
        self.assertEqual("experimental", args.skill_builder_command)
        self.assertEqual("probe-codex-trigger", args.experimental_command)
        self.assertEqual("develop-web-game", args.skill)
        self.assertEqual(["game-bootstrap"], args.with_skill)
        self.assertEqual("gpt-5.4", args.model)

    def test_skill_builder_experimental_analyze_codex_run_parses(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "skill-builder",
                "experimental",
                "analyze-codex-run",
                "tmp/run.jsonl",
                "--output",
                "tmp/run.skill-trace.json",
            ]
        )

        self.assertEqual("skill-builder", args.command)
        self.assertEqual("experimental", args.skill_builder_command)
        self.assertEqual("analyze-codex-run", args.experimental_command)
        self.assertEqual("tmp/run.jsonl", args.source_path)
        self.assertEqual("tmp/run.skill-trace.json", args.output)

    def test_skill_builder_experimental_analyze_codex_corpus_parses(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "skill-builder",
                "experimental",
                "analyze-codex-corpus",
                "--manifest",
                "tests/system/codex_skill_corpus.json",
                "--output-dir",
                "tmp/corpus-report",
            ]
        )

        self.assertEqual("skill-builder", args.command)
        self.assertEqual("experimental", args.skill_builder_command)
        self.assertEqual("analyze-codex-corpus", args.experimental_command)
        self.assertEqual("tests/system/codex_skill_corpus.json", args.manifest)
        self.assertEqual("tmp/corpus-report", args.output_dir)

    def test_skill_builder_experimental_find_near_dupe_skills_parses(self) -> None:
        parser = build_parser()

        args = parser.parse_args(
            [
                "skill-builder",
                "experimental",
                "find-near-dupe-skills",
                "--skills-root",
                "/tmp/.codex/skills",
                "--area",
                ".system",
                "--area",
                "root",
                "--output",
                "tmp/skill-near-dupes/report.json",
            ]
        )

        self.assertEqual("skill-builder", args.command)
        self.assertEqual("experimental", args.skill_builder_command)
        self.assertEqual("find-near-dupe-skills", args.experimental_command)
        self.assertEqual("/tmp/.codex/skills", args.skills_root)
        self.assertEqual([".system", "root"], args.area)
        self.assertEqual("tmp/skill-near-dupes/report.json", args.output)


class CliMainTests(unittest.TestCase):
    def _run_main(self, argv: list[str]) -> tuple[int, str]:
        stdout = io.StringIO()
        with mock.patch.object(sys, "argv", ["molt", *argv]), mock.patch("sys.stdout", stdout):
            code = cli.main()
        return code, stdout.getvalue()

    def test_parse_overrides_overwrites_duplicate_keys(self) -> None:
        self.assertEqual(
            {"target": "repo", "mode": "slow"},
            cli.parse_overrides(["target=repo", "mode=fast", "mode=slow"]),
        )

    def test_parse_overrides_rejects_invalid_value(self) -> None:
        with self.assertRaises(ValueError):
            cli.parse_overrides(["missing-equals"])

    def test_main_run_command_prints_result_and_returns_status_code(self) -> None:
        for status, expected_code in [("completed", 0), ("failed", 1)]:
            with self.subTest(status=status):
                result = SimpleNamespace(
                    run_id="run-1",
                    workflow="manual-triage",
                    agent="triage-worker",
                    status=status,
                    run_path="runs/run-1.json",
                    log_path="logs/2026-03-28/run-1.json",
                    output={"summary": f"{status} summary"},
                )
                with mock.patch("moltfarm.runner.run_workflow", return_value=result) as patched:
                    code, stdout = self._run_main(
                        [
                            "skill-builder",
                            "run",
                            "manual-triage",
                            "--input",
                            "target=repo",
                            "--input",
                            "mode=fast",
                        ]
                    )

                self.assertEqual(expected_code, code)
                patched.assert_called_once_with(
                    project_root=Path.cwd(),
                    workflow_name="manual-triage",
                    overrides={"target": "repo", "mode": "fast"},
                )
                self.assertEqual(
                    {
                        "run_id": "run-1",
                        "workflow": "manual-triage",
                        "agent": "triage-worker",
                        "status": status,
                        "run_path": "runs/run-1.json",
                        "log_path": "logs/2026-03-28/run-1.json",
                        "summary": f"{status} summary",
                    },
                    json.loads(stdout),
                )

    def test_main_eval_skill_dispatches(self) -> None:
        result = {"skill": "run-summarizer", "status": "ok"}
        with mock.patch("moltfarm.skill_evaluator.evaluate_skill", return_value=result) as patched:
            code, stdout = self._run_main(
                [
                    "skill-builder",
                    "eval-skill",
                    "run-summarizer",
                    "--baseline",
                    "snapshot",
                    "--snapshot-current",
                    "--model",
                    "gpt-5.4",
                    "--grader-model",
                    "gpt-5.4-mini",
                ]
            )

        self.assertEqual(0, code)
        patched.assert_called_once_with(
            project_root=Path.cwd(),
            skill_name="run-summarizer",
            model="gpt-5.4",
            grader_model="gpt-5.4-mini",
            baseline="snapshot",
            snapshot_current=True,
        )
        self.assertEqual(result, json.loads(stdout))

    def test_main_create_evals_dispatches(self) -> None:
        result = {"session_id": "session-1", "phase": "draft_ready"}
        with mock.patch("moltfarm.eval_authoring.create_evals", return_value=result) as patched:
            code, stdout = self._run_main(
                [
                    "skill-builder",
                    "create-evals",
                    "run-summarizer",
                    "--session",
                    "session-1",
                    "--answer",
                    "selected_flavors=core-task",
                    "--answer",
                    "author_notes=keep-it-local",
                    "--promote",
                    "--model",
                    "gpt-5.4",
                ]
            )

        self.assertEqual(0, code)
        patched.assert_called_once_with(
            project_root=Path.cwd(),
            skill_name="run-summarizer",
            session_id="session-1",
            answers={"selected_flavors": "core-task", "author_notes": "keep-it-local"},
            promote=True,
            model="gpt-5.4",
        )
        self.assertEqual(result, json.loads(stdout))

    def test_main_promote_system_map_dispatches(self) -> None:
        result = {"session_id": "session-1", "status": "completed"}
        with mock.patch("moltfarm.wiki_system_map.promote_system_map", return_value=result) as patched:
            code, stdout = self._run_main(
                [
                    "skill-builder",
                    "promote-system-map",
                    "--session",
                    "session-1",
                ]
            )

        self.assertEqual(0, code)
        patched.assert_called_once_with(
            project_root=Path.cwd(),
            session_id="session-1",
        )
        self.assertEqual(result, json.loads(stdout))

    def test_main_analyze_codex_run_dispatches(self) -> None:
        result = {"timeline_path": "tmp/run.skill-trace.json"}
        with (
            mock.patch(
                "moltfarm.experimental.codex_timeline.discover_analysis_skill_names",
                return_value=["analyze-a", "analyze-b"],
            ) as patched_discover,
            mock.patch(
                "moltfarm.experimental.codex_timeline.write_codex_skill_timeline",
                return_value=result,
            ) as patched_write,
        ):
            code, stdout = self._run_main(
                [
                    "skill-builder",
                    "experimental",
                    "analyze-codex-run",
                    "tmp/run.jsonl",
                    "--output",
                    "tmp/run.skill-trace.json",
                ]
            )

        self.assertEqual(0, code)
        patched_discover.assert_called_once_with(project_root=Path.cwd())
        patched_write.assert_called_once_with(
            Path("tmp/run.jsonl"),
            skill_names=["analyze-a", "analyze-b"],
            output_path=Path("tmp/run.skill-trace.json"),
        )
        self.assertEqual(result, json.loads(stdout))

    def test_main_analyze_codex_corpus_returns_failure_code_when_report_fails(self) -> None:
        result = {"passed": False, "cases": []}
        with mock.patch("moltfarm.experimental.codex_corpus.analyze_codex_corpus", return_value=result) as patched:
            code, stdout = self._run_main(
                [
                    "skill-builder",
                    "experimental",
                    "analyze-codex-corpus",
                    "--manifest",
                    "tests/system/codex_skill_corpus.json",
                    "--output-dir",
                    "tmp/corpus-report",
                ]
            )

        self.assertEqual(1, code)
        patched.assert_called_once_with(
            project_root=Path.cwd(),
            manifest_path=Path("tests/system/codex_skill_corpus.json"),
            output_dir=Path("tmp/corpus-report"),
        )
        self.assertEqual(result, json.loads(stdout))

    def test_main_probe_codex_trigger_returns_failure_code_when_probe_is_incomplete(self) -> None:
        result = {"discover_completed": False, "run_id": "probe-1"}
        with mock.patch(
            "moltfarm.experimental.codex_probe.run_codex_trigger_probe",
            return_value=result,
        ) as patched:
            code, stdout = self._run_main(
                [
                    "skill-builder",
                    "experimental",
                    "probe-codex-trigger",
                    "develop-web-game",
                    "--with-skill",
                    "game-bootstrap",
                    "--model",
                    "gpt-5.4",
                ]
            )

        self.assertEqual(1, code)
        patched.assert_called_once_with(
            project_root=Path.cwd(),
            target_skill="develop-web-game",
            installed_skills=["game-bootstrap"],
            model="gpt-5.4",
        )
        self.assertEqual(result, json.loads(stdout))

    def test_main_find_near_dupe_skills_dispatches(self) -> None:
        result = {"pairs": []}
        with mock.patch(
            "moltfarm.experimental.near_dupe_skills.write_skill_near_dupe_report",
            return_value=result,
        ) as patched:
            code, stdout = self._run_main(
                [
                    "skill-builder",
                    "experimental",
                    "find-near-dupe-skills",
                    "--skills-root",
                    "/tmp/.codex/skills",
                    "--area",
                    ".system",
                    "--output",
                    "tmp/report.json",
                ]
            )

        self.assertEqual(0, code)
        patched.assert_called_once_with(
            project_root=Path.cwd(),
            skills_root=Path("/tmp/.codex/skills"),
            areas=[".system"],
            output_path=Path("tmp/report.json"),
        )
        self.assertEqual(result, json.loads(stdout))

    def test_main_find_near_dupe_skills_uses_parser_error_for_user_input_failures(self) -> None:
        def raising_error(self, message):
            raise RuntimeError(message)

        with (
            mock.patch(
                "moltfarm.experimental.near_dupe_skills.write_skill_near_dupe_report",
                side_effect=ValueError("bad skills root"),
            ),
            mock.patch("argparse.ArgumentParser.error", new=raising_error),
        ):
            with self.assertRaises(RuntimeError) as raised:
                self._run_main(
                    [
                        "skill-builder",
                        "experimental",
                        "find-near-dupe-skills",
                        "--skills-root",
                        "/tmp/.codex/skills",
                    ]
                )

        self.assertEqual("bad skills root", str(raised.exception))

    def test_main_unknown_command_uses_parser_error(self) -> None:
        class FakeParser:
            def parse_args(self):
                return SimpleNamespace(command="mystery")

            def error(self, message):
                raise RuntimeError(message)

        with mock.patch.object(cli, "build_parser", return_value=FakeParser()):
            with self.assertRaises(RuntimeError) as raised:
                cli.main()

        self.assertEqual("Unknown command: mystery", str(raised.exception))

    def test_module_entrypoint_raises_system_exit(self) -> None:
        result = SimpleNamespace(
            run_id="run-1",
            workflow="manual-triage",
            agent="triage-worker",
            status="completed",
            run_path="runs/run-1.json",
            log_path="logs/2026-03-28/run-1.json",
            output={"summary": "completed summary"},
        )
        stdout = io.StringIO()
        with (
            mock.patch.object(sys, "argv", ["molt", "skill-builder", "run", "manual-triage"]),
            mock.patch("sys.stdout", stdout),
            mock.patch("moltfarm.runner.run_workflow", return_value=result),
        ):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                with self.assertRaises(SystemExit) as raised:
                    runpy.run_module("moltfarm.cli", run_name="__main__")

        self.assertEqual(0, raised.exception.code)


if __name__ == "__main__":
    unittest.main()
