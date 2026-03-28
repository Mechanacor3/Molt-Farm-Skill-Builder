from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm.experimental.codex_timeline import analyze_codex_jsonl, write_codex_skill_timeline


class ExperimentalCodexTimelineTests(unittest.TestCase):
    def test_analyze_codex_jsonl_builds_ordered_skill_timeline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "trigger.jsonl"
            source_path.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "thread.started", "thread_id": "t"}),
                        "not-json",
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_0",
                                    "type": "agent_message",
                                    "text": "Using `develop-web-game` because the request is for a browser game.",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "item.started",
                                "item": {
                                    "id": "item_1",
                                    "type": "command_execution",
                                    "command": "/bin/bash -lc \"sed -n '1,220p' /tmp/.agents/skills/develop-web-game/SKILL.md\"",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_1",
                                    "type": "command_execution",
                                    "command": "/bin/bash -lc \"sed -n '1,220p' /tmp/.agents/skills/develop-web-game/SKILL.md\"",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_2",
                                    "type": "command_execution",
                                    "command": "/bin/bash -lc \"sed -n '1,220p' /tmp/.agents/skills/develop-web-game/references/dev-loop.md\"",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "turn.completed",
                                "usage": {"input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 3},
                            }
                        ),
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_3",
                                    "type": "agent_message",
                                    "text": "Using `playwright-eval-loop` after the first playable slice is stable.",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_4",
                                    "type": "command_execution",
                                    "command": "/bin/bash -lc \"sed -n '1,220p' /tmp/.agents/skills/playwright-eval-loop/SKILL.md\"",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "turn.completed",
                                "usage": {"input_tokens": 20, "cached_input_tokens": 4, "output_tokens": 5},
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            payload = analyze_codex_jsonl(
                source_path,
                skill_names=["develop-web-game", "playwright-eval-loop"],
            )

            self.assertEqual("codex_jsonl", payload["detected_format"])
            self.assertEqual("exec", payload["source_variant"])
            self.assertEqual(1, payload["analysis_version"])
            self.assertEqual(2, payload["completed_turns"])
            self.assertEqual(
                [1, 2],
                [entry["turn_index"] for entry in payload["usage_by_turn"]],
            )
            self.assertEqual(
                [
                    "agent_skill_claim",
                    "skill_file_read",
                    "skill_resource_read",
                    "agent_skill_claim",
                    "skill_file_read",
                ],
                [event["event_type"] for event in payload["events"]],
            )
            self.assertEqual(
                [1, 2, 3, 4, 5],
                [event["index"] for event in payload["events"]],
            )
            self.assertEqual(
                ["develop-web-game", "develop-web-game", "playwright-eval-loop"],
                payload["observed_invocation_order"],
            )
            self.assertEqual(
                ["develop-web-game", "playwright-eval-loop"],
                payload["first_seen_skill_order"],
            )
            self.assertEqual(3, payload["skills"]["develop-web-game"]["event_count"])
            self.assertEqual(2, payload["skills"]["develop-web-game"]["invocation_event_count"])
            self.assertTrue(payload["skills"]["develop-web-game"]["has_invocation"])

    def test_claim_only_log_keeps_claim_but_no_invocation_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "claim-only.jsonl"
            source_path.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_0",
                                    "type": "agent_message",
                                    "text": "Using `develop-web-game` for the first pass.",
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            payload = analyze_codex_jsonl(
                source_path,
                skill_names=["develop-web-game"],
            )

            self.assertEqual(1, len(payload["events"]))
            self.assertEqual("exec", payload["source_variant"])
            self.assertEqual("agent_skill_claim", payload["events"][0]["event_type"])
            self.assertEqual([], payload["observed_invocation_order"])
            self.assertEqual([], payload["first_seen_skill_order"])
            self.assertFalse(payload["skills"]["develop-web-game"]["has_invocation"])

    def test_analyze_codex_jsonl_detects_codex_home_skill_reads_in_one_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "autotrigger.jsonl"
            source_path.write_text(
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
                                        "/bin/bash -lc \"sed -n '1,240p' "
                                        "/home/node/.codex/skills/develop-web-game/SKILL.md; "
                                        "echo '---SKILL-SPLIT---'; "
                                        "sed -n '1,240p' /home/node/.codex/skills/playwright/SKILL.md\""
                                    ),
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            payload = analyze_codex_jsonl(
                source_path,
                skill_names=["develop-web-game"],
            )

            self.assertEqual("exec", payload["source_variant"])
            self.assertEqual(
                ["develop-web-game", "playwright"],
                payload["observed_invocation_order"],
            )
            self.assertEqual(
                ["develop-web-game", "playwright"],
                payload["first_seen_skill_order"],
            )

    def test_analyze_codex_jsonl_resolves_namespaced_codex_home_skill_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "namespaced.jsonl"
            source_path.write_text(
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
                                        "/home/user/.codex/skills/.system/skill-creator/SKILL.md\""
                                    ),
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            payload = analyze_codex_jsonl(
                source_path,
                skill_names=["skill-creator"],
            )

            self.assertEqual(["skill-creator"], payload["observed_invocation_order"])
            self.assertEqual("skill_file_read", payload["events"][0]["event_type"])
            self.assertEqual("skill-creator", payload["events"][0]["skill_name"])

    def test_analyze_codex_jsonl_normalizes_archived_session_events(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "archived.jsonl"
            source_path.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "type": "response_item",
                                "payload": {
                                    "type": "message",
                                    "role": "user",
                                    "content": [
                                        {
                                            "type": "input_text",
                                            "text": "file: /home/user/.codex/skills/.system/skill-creator/SKILL.md",
                                        }
                                    ],
                                },
                            }
                        ),
                        json.dumps({"type": "turn_context", "payload": {"turn_id": "turn-1"}}),
                        json.dumps(
                            {
                                "type": "event_msg",
                                "payload": {
                                    "type": "agent_message",
                                    "message": "Using `skill-creator` for this workflow.",
                                },
                            }
                        ),
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
                        json.dumps({"type": "turn_context", "payload": {"turn_id": "turn-2"}}),
                        json.dumps(
                            {
                                "type": "response_item",
                                "payload": {
                                    "type": "function_call",
                                    "name": "multi_tool_use.parallel",
                                    "call_id": "call_2",
                                    "arguments": json.dumps(
                                        {
                                            "tool_uses": [
                                                {
                                                    "recipient_name": "functions.exec_command",
                                                    "parameters": {
                                                        "cmd": (
                                                            "sed -n '1,120p' "
                                                            "/home/user/.codex/skills/develop-web-game/SKILL.md"
                                                        )
                                                    },
                                                },
                                                {
                                                    "recipient_name": "functions.exec_command",
                                                    "parameters": {
                                                        "cmd": (
                                                            "sed -n '1,120p' "
                                                            "/home/user/.codex/skills/playwright/SKILL.md"
                                                        )
                                                    },
                                                },
                                            ]
                                        }
                                    ),
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            payload = analyze_codex_jsonl(
                source_path,
                skill_names=["skill-creator", "develop-web-game"],
            )

            self.assertEqual("archived_session", payload["source_variant"])
            self.assertEqual(2, payload["completed_turns"])
            self.assertEqual([], payload["usage_by_turn"])
            self.assertEqual(
                ["skill-creator", "develop-web-game", "playwright"],
                payload["observed_invocation_order"],
            )
            self.assertEqual(
                ["skill-creator", "develop-web-game", "playwright"],
                payload["first_seen_skill_order"],
            )
            self.assertEqual("agent_skill_claim", payload["events"][0]["event_type"])
            self.assertEqual("skill-creator", payload["events"][0]["skill_name"])

    def test_write_codex_skill_timeline_uses_default_sidecar_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "trigger.jsonl"
            source_path.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_1",
                                    "type": "command_execution",
                                    "command": "/bin/bash -lc \"sed -n '1,220p' /tmp/.agents/skills/develop-web-game/SKILL.md\"",
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            result = write_codex_skill_timeline(
                source_path,
                skill_names=["develop-web-game"],
            )

            output_path = Path(result["output_path"])
            self.assertEqual("trigger.skill-trace.json", output_path.name)
            self.assertTrue(output_path.is_file())
            written = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(["develop-web-game"], written["observed_invocation_order"])

    def test_write_codex_skill_timeline_honors_explicit_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source_path = Path(temp_dir) / "trigger.jsonl"
            output_path = Path(temp_dir) / "artifacts" / "timeline.json"
            source_path.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_1",
                                    "type": "command_execution",
                                    "command": "/bin/bash -lc \"sed -n '1,220p' /tmp/.agents/skills/develop-web-game/references/dev-loop.md\"",
                                },
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            result = write_codex_skill_timeline(
                source_path,
                skill_names=["develop-web-game"],
                output_path=output_path,
            )

            self.assertEqual(str(output_path.resolve()), result["output_path"])
            self.assertTrue(output_path.is_file())
