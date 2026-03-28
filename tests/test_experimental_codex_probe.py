from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm.experimental.codex_probe import run_codex_trigger_probe, summarize_codex_trigger_probe


class ExperimentalCodexProbeTests(unittest.TestCase):
    def test_summarize_codex_trigger_probe_reports_first_skill_read(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            sandbox_root = Path(temp_dir)
            discover_log = sandbox_root / "discover.jsonl"
            trigger_log = sandbox_root / "trigger.jsonl"
            discover_log.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "thread.started", "thread_id": "t1"}),
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_0",
                                    "type": "agent_message",
                                    "text": "- `develop-web-game`: coordination",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "turn.completed",
                                "usage": {"input_tokens": 10, "cached_input_tokens": 2, "output_tokens": 3},
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )
            trigger_log.write_text(
                "\n".join(
                    [
                        json.dumps({"type": "thread.started", "thread_id": "t2"}),
                        json.dumps({"type": "turn.started"}),
                        json.dumps(
                            {
                                "type": "item.completed",
                                "item": {
                                    "id": "item_0",
                                    "type": "agent_message",
                                    "text": "Using `develop-web-game` because this is a browser game request.",
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
                                "type": "turn.completed",
                                "usage": {"input_tokens": 20, "cached_input_tokens": 4, "output_tokens": 5},
                            }
                        ),
                    ]
                ),
                encoding="utf-8",
            )

            summary = summarize_codex_trigger_probe(
                sandbox_root=sandbox_root,
                target_skill="develop-web-game",
                installed_skills=["develop-web-game", "game-bootstrap"],
                discover_log=discover_log,
                trigger_log=trigger_log,
                discover_exit_code=0,
                trigger_exit_code=0,
            )

            self.assertTrue(summary["target_triggered_first"])
            self.assertEqual("develop-web-game", summary["first_read_skill"])
            self.assertTrue(summary["first_message_mentions_target"])

    def test_run_codex_trigger_probe_creates_summary(self) -> None:
        original_runner = __import__(
            "moltfarm.experimental.codex_probe",
            fromlist=["_run_codex_exec"],
        )
        original_run_codex_exec = original_runner._run_codex_exec
        try:
            def fake_run_codex_exec(*, sandbox_root, prompt_path, output_path, model):
                del model
                text = prompt_path.read_text(encoding="utf-8")
                if "What skills are available" in text:
                    output_path.write_text(
                        "\n".join(
                            [
                                json.dumps({"type": "thread.started", "thread_id": "d"}),
                                json.dumps({"type": "turn.started"}),
                                json.dumps(
                                    {
                                        "type": "item.completed",
                                        "item": {
                                            "id": "item_0",
                                            "type": "agent_message",
                                            "text": "- `develop-web-game`: coordination",
                                        },
                                    }
                                ),
                                json.dumps(
                                    {
                                        "type": "turn.completed",
                                        "usage": {
                                            "input_tokens": 1,
                                            "cached_input_tokens": 0,
                                            "output_tokens": 1,
                                        },
                                    }
                                ),
                            ]
                        ),
                        encoding="utf-8",
                    )
                else:
                    output_path.write_text(
                        "\n".join(
                            [
                                json.dumps({"type": "thread.started", "thread_id": "t"}),
                                json.dumps({"type": "turn.started"}),
                                json.dumps(
                                    {
                                        "type": "item.completed",
                                        "item": {
                                            "id": "item_0",
                                            "type": "agent_message",
                                            "text": "Using `develop-web-game` because this is a browser game request.",
                                        },
                                    }
                                ),
                                json.dumps(
                                    {
                                        "type": "item.completed",
                                        "item": {
                                            "id": "item_1",
                                            "type": "command_execution",
                                            "command": f"/bin/bash -lc \"sed -n '1,220p' {sandbox_root}/.agents/skills/develop-web-game/SKILL.md\"",
                                        },
                                    }
                                ),
                            ]
                        ),
                        encoding="utf-8",
                    )
                return 0

            original_runner._run_codex_exec = fake_run_codex_exec

            with tempfile.TemporaryDirectory() as temp_dir:
                project_root = Path(temp_dir)
                for skill_name in ["develop-web-game", "game-bootstrap"]:
                    skill_dir = project_root / "skills" / skill_name
                    skill_dir.mkdir(parents=True, exist_ok=True)
                    (skill_dir / "SKILL.md").write_text(
                        f"---\nname: {skill_name}\ndescription: test\n---\n\nUse it.\n",
                        encoding="utf-8",
                    )
                fixture_root = project_root / "experiments" / "codex-trigger-probe" / "develop-web-game"
                fixture_root.mkdir(parents=True, exist_ok=True)
                (fixture_root / "discover.md").write_text("What skills are available?", encoding="utf-8")
                (fixture_root / "trigger.md").write_text("Build a tiny browser game.", encoding="utf-8")

                summary = run_codex_trigger_probe(
                    project_root,
                    target_skill="develop-web-game",
                    installed_skills=["game-bootstrap"],
                )

                self.assertTrue(summary["target_triggered_first"])
                self.assertTrue((project_root / summary["summary_path"]).is_file())
        finally:
            original_runner._run_codex_exec = original_run_codex_exec


if __name__ == "__main__":
    unittest.main()
