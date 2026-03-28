from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

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


if __name__ == "__main__":
    unittest.main()
