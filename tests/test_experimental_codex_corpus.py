from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm.experimental.codex_corpus import analyze_codex_corpus


class ExperimentalCodexCorpusTests(unittest.TestCase):
    def test_analyze_codex_corpus_writes_report_and_case_timelines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_skill(project_root / "skills" / "develop-web-game" / "SKILL.md", "develop-web-game")
            log_path = project_root / "fixtures" / "run.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_1",
                                    "type": "command_execution",
                                    "command": (
                                        "/bin/bash -lc \"sed -n '1,120p' "
                                        "/tmp/.agents/skills/develop-web-game/SKILL.md\""
                                    ),
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )
            manifest_path = project_root / "tests" / "system" / "corpus.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "id": "synthetic",
                                "path": "fixtures/run.jsonl",
                                "description": "Simple repo-local skill read.",
                                "expected_observed_invocation_order": ["develop-web-game"],
                                "expected_first_seen_skill_order": ["develop-web-game"],
                                "min_invocation_event_count": 1,
                                "max_invocation_event_count": 1,
                            }
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            result = analyze_codex_corpus(
                project_root,
                manifest_path=manifest_path,
            )

            self.assertTrue(result["passed"])
            self.assertTrue(Path(result["report_path"]).is_file())
            self.assertTrue(Path(result["report_markdown_path"]).is_file())
            self.assertEqual([], result["failed_case_ids"])
            self.assertTrue(
                (Path(result["output_dir"]) / "cases" / "synthetic.skill-trace.json").is_file()
            )

    def test_analyze_codex_corpus_expands_home_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir) / "repo"
            home_root = Path(temp_dir) / "home"
            project_root.mkdir(parents=True, exist_ok=True)
            home_root.mkdir(parents=True, exist_ok=True)
            _write_skill(project_root / "skills" / "skill-creator" / "SKILL.md", "skill-creator")

            log_path = home_root / "archived.jsonl"
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "turn_context", "payload": {"turn_id": "turn-1"}}),
                        json.dumps(
                            {
                                "type": "response_item",
                                "payload": {
                                    "type": "function_call",
                                    "name": "exec_command",
                                    "call_id": "call_1",
                                    "arguments": json.dumps(
                                        {
                                            "cmd": (
                                                "sed -n '1,120p' "
                                                "/home/user/.codex/skills/.system/skill-creator/SKILL.md"
                                            )
                                        }
                                    ),
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )
            manifest_path = project_root / "tests" / "system" / "corpus.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "id": "home-case",
                                "path": "$HOME/archived.jsonl",
                                "expected_observed_invocation_order": ["skill-creator"],
                                "min_invocation_event_count": 1,
                            }
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"HOME": str(home_root)}, clear=False):
                result = analyze_codex_corpus(
                    project_root,
                    manifest_path=manifest_path,
                )

            self.assertTrue(result["passed"])
            self.assertEqual(
                ["skill-creator"],
                result["results"][0]["actual_observed_invocation_order"],
            )

    def test_analyze_codex_corpus_fails_for_missing_logs_and_mismatches(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            _write_skill(project_root / "skills" / "develop-web-game" / "SKILL.md", "develop-web-game")

            log_path = project_root / "fixtures" / "run.jsonl"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            log_path.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_1",
                                    "type": "command_execution",
                                    "command": (
                                        "/bin/bash -lc \"sed -n '1,120p' "
                                        "/tmp/.agents/skills/develop-web-game/SKILL.md\""
                                    ),
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            manifest_path = project_root / "tests" / "system" / "corpus.json"
            manifest_path.parent.mkdir(parents=True, exist_ok=True)
            manifest_path.write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "id": "mismatch",
                                "path": "fixtures/run.jsonl",
                                "expected_observed_invocation_order": ["playwright"],
                            },
                            {
                                "id": "missing",
                                "path": "fixtures/missing.jsonl",
                                "expected_observed_invocation_order": [],
                            },
                        ]
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            result = analyze_codex_corpus(
                project_root,
                manifest_path=manifest_path,
            )

            self.assertFalse(result["passed"])
            self.assertEqual(["missing"], result["missing_case_ids"])
            self.assertEqual({"mismatch", "missing"}, set(result["failed_case_ids"]))


def _write_skill(skill_path: Path, skill_name: str) -> None:
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(
        f"---\nname: {skill_name}\ndescription: test\n---\n\nUse it.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
