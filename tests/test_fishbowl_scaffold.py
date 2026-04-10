from __future__ import annotations

import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FISHBOWL_ROOT = PROJECT_ROOT / "fishbowl"


class FishbowlScaffoldTests(unittest.TestCase):
    def test_opencode_config_parses_and_locks_local_defaults(self) -> None:
        payload = json.loads((FISHBOWL_ROOT / "opencode.json").read_text(encoding="utf-8"))

        self.assertEqual("overseer", payload["default_agent"])
        self.assertEqual("llama.cpp/gemma-4-e4b", payload["model"])
        self.assertEqual("llama.cpp/gemma-4-e4b", payload["small_model"])
        self.assertEqual("disabled", payload["share"])
        self.assertEqual(["llama.cpp"], payload["enabled_providers"])
        self.assertEqual("deny", payload["permission"]["skill"]["*"])
        self.assertEqual("deny", payload["permission"]["task"]["*"])
        self.assertEqual("ask", payload["permission"]["bash"]["*"])
        self.assertEqual("ask", payload["permission"]["edit"]["*"])
        self.assertEqual("deny", payload["permission"]["webfetch"])
        self.assertEqual("deny", payload["permission"]["websearch"])

    def test_fishbowl_agents_and_skills_exist(self) -> None:
        agent_paths = [
            FISHBOWL_ROOT / ".opencode" / "agents" / "overseer.md",
            FISHBOWL_ROOT / ".opencode" / "agents" / "shipwright.md",
            FISHBOWL_ROOT / ".opencode" / "agents" / "scout.md",
            FISHBOWL_ROOT / ".opencode" / "agents" / "scribe.md",
        ]
        skill_paths = [
            FISHBOWL_ROOT / ".opencode" / "skills" / "fishbowl-overseer" / "SKILL.md",
            FISHBOWL_ROOT / ".opencode" / "skills" / "fishbowl-builder" / "SKILL.md",
            FISHBOWL_ROOT / ".opencode" / "skills" / "fishbowl-browser-check" / "SKILL.md",
            FISHBOWL_ROOT / ".opencode" / "skills" / "fishbowl-journal" / "SKILL.md",
        ]

        for path in agent_paths + skill_paths:
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), f"Missing fishbowl scaffold file: {path}")

    def test_target_template_has_required_keys(self) -> None:
        payload = json.loads((FISHBOWL_ROOT / "config" / "target.example.json").read_text(encoding="utf-8"))

        self.assertEqual(
            {
                "project_name",
                "repo_path",
                "package_manager",
                "dev_command",
                "dev_url",
                "test_command",
                "notes",
            },
            set(payload),
        )
        gitignore = (FISHBOWL_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("config/target.local.json", gitignore)

    def test_journal_scaffold_exists(self) -> None:
        expected_paths = [
            FISHBOWL_ROOT / "journal" / "backlog.md",
            FISHBOWL_ROOT / "journal" / "decisions.md",
            FISHBOWL_ROOT / "journal" / "lesson-candidates.md",
            FISHBOWL_ROOT / "journal" / "plans" / "2026-04-10-molt-farm-visualization-plan.md",
            FISHBOWL_ROOT / "journal" / "templates" / "session-template.md",
            FISHBOWL_ROOT / "journal" / "sessions" / "2026-04-10-kickoff.md",
            FISHBOWL_ROOT / "journal" / "sessions" / "2026-04-10-metaphor-visual-plan.md",
            FISHBOWL_ROOT / "journal" / "sessions" / "2026-04-10-opencode-smoke-rounds-followup.md",
        ]

        for path in expected_paths:
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), f"Missing journal scaffold file: {path}")

        template = (FISHBOWL_ROOT / "journal" / "templates" / "session-template.md").read_text(encoding="utf-8")
        for field_name in ["goal:", "attempted:", "evidence_paths:", "decision:", "next:"]:
            with self.subTest(field_name=field_name):
                self.assertIn(field_name, template)

    def test_visualization_plan_captures_core_mapping(self) -> None:
        plan = (
            FISHBOWL_ROOT / "journal" / "plans" / "2026-04-10-molt-farm-visualization-plan.md"
        ).read_text(encoding="utf-8")

        self.assertIn("islands = agents", plan)
        self.assertIn("crops = skills", plan)
        self.assertIn("boats = agent-agent communication", plan)
        self.assertIn("farm-state.json", plan)
        self.assertIn("farm-events.jsonl", plan)

    def test_agent_contracts_lock_config_location_and_output_shape(self) -> None:
        overseer_agent = (FISHBOWL_ROOT / ".opencode" / "agents" / "overseer.md").read_text(encoding="utf-8")
        shipwright_agent = (FISHBOWL_ROOT / ".opencode" / "agents" / "shipwright.md").read_text(encoding="utf-8")
        scout_agent = (FISHBOWL_ROOT / ".opencode" / "agents" / "scout.md").read_text(encoding="utf-8")
        overseer_skill = (
            FISHBOWL_ROOT / ".opencode" / "skills" / "fishbowl-overseer" / "SKILL.md"
        ).read_text(encoding="utf-8")
        builder_skill = (
            FISHBOWL_ROOT / ".opencode" / "skills" / "fishbowl-builder" / "SKILL.md"
        ).read_text(encoding="utf-8")
        browser_check_skill = (
            FISHBOWL_ROOT / ".opencode" / "skills" / "fishbowl-browser-check" / "SKILL.md"
        ).read_text(encoding="utf-8")

        self.assertIn("not from inside `repo_path`", overseer_agent)
        self.assertIn('Task(description="...", prompt="...", subagent_type="...")', overseer_agent)
        self.assertIn("not from inside `repo_path`", overseer_skill)
        self.assertIn('Task(description="...", prompt="...", subagent_type="...")', overseer_skill)
        self.assertIn("Do not look for it inside `repo_path`", shipwright_agent)
        self.assertIn("Do not look for it inside the target repo", scout_agent)
        self.assertIn("Return only the six required lines.", builder_skill)
        self.assertIn("Return only the five required lines.", browser_check_skill)


if __name__ == "__main__":
    unittest.main()
