from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm.cli import main
from moltfarm.experimental.near_dupe_skills import analyze_skill_near_dupes


class ExperimentalNearDupeSkillTests(unittest.TestCase):
    def test_analyze_skill_near_dupes_reports_same_name_pair_as_high(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skills_root = Path(temp_dir) / "skills"
            _write_skill(
                skills_root / "shared-skill" / "SKILL.md",
                name="shared-skill",
                description="Package one local Python CLI with narrow scope.",
                trigger_lines=[
                    "A local Python CLI needs packaging.",
                    "The work should stay narrow and inspectable.",
                ],
                instruction_lines=[
                    "Inspect pyproject.toml and existing entrypoints.",
                    "Prefer small packaging changes over broad rewrites.",
                ],
            )
            _write_skill(
                skills_root / ".system" / "shared-copy" / "SKILL.md",
                name="shared-skill",
                description="Package one local Python CLI with narrow scope.",
                trigger_lines=[
                    "A local Python CLI needs packaging.",
                    "The work should stay narrow and inspectable.",
                ],
                instruction_lines=[
                    "Inspect pyproject.toml and existing entrypoints.",
                    "Prefer small packaging changes over broad rewrites.",
                ],
            )

            result = analyze_skill_near_dupes(skills_root)

            self.assertEqual(2, result["skill_count"])
            self.assertEqual(1, result["candidate_pair_count"])
            pair = result["pairs"][0]
            self.assertTrue(pair["same_name"])
            self.assertEqual("high", pair["severity"])
            self.assertEqual(
                {".system", "root"},
                {pair["left"]["area"], pair["right"]["area"]},
            )

    def test_analyze_skill_near_dupes_skips_low_overlap_pairs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skills_root = Path(temp_dir) / "skills"
            _write_skill(
                skills_root / "browser-game" / "SKILL.md",
                name="browser-game-maker",
                description="Build a tiny browser arcade game with one mechanic.",
                trigger_lines=[
                    "A small browser game needs a playable loop.",
                    "The request is for a game jam toy.",
                ],
                instruction_lines=[
                    "Start with one control scheme and one fail state.",
                    "Keep the prototype easy to replay.",
                ],
            )
            _write_skill(
                skills_root / "ledger-audit" / "SKILL.md",
                name="ledger-audit",
                description="Review bookkeeping ledgers for missing invoices and tax mismatches.",
                trigger_lines=[
                    "A finance export needs reconciliation.",
                    "The main issue is invoice accuracy.",
                ],
                instruction_lines=[
                    "Check account totals against the general ledger.",
                    "List missing invoices and tax discrepancies.",
                ],
            )

            result = analyze_skill_near_dupes(skills_root)

            self.assertEqual(2, result["skill_count"])
            self.assertEqual([], result["pairs"])

    def test_analyze_skill_near_dupes_filters_to_selected_areas(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skills_root = Path(temp_dir) / "skills"
            shared_description = "Package one local Python CLI with narrow scope."
            shared_trigger = [
                "A local Python CLI needs packaging.",
                "The work should stay narrow and inspectable.",
            ]
            shared_instructions = [
                "Inspect pyproject.toml and existing entrypoints.",
                "Prefer small packaging changes over broad rewrites.",
            ]
            _write_skill(
                skills_root / "root-builder" / "SKILL.md",
                name="root-builder",
                description=shared_description,
                trigger_lines=shared_trigger,
                instruction_lines=shared_instructions,
            )
            _write_skill(
                skills_root / ".system" / "system-builder" / "SKILL.md",
                name="system-builder",
                description=shared_description,
                trigger_lines=shared_trigger,
                instruction_lines=shared_instructions,
            )
            _write_skill(
                skills_root / ".curated" / "curated-builder" / "SKILL.md",
                name="curated-builder",
                description=shared_description,
                trigger_lines=shared_trigger,
                instruction_lines=shared_instructions,
            )

            result = analyze_skill_near_dupes(skills_root, areas=["root", ".system"])

            self.assertEqual(["root", ".system"], result["selected_areas"])
            self.assertEqual(2, result["skill_count"])
            self.assertEqual(1, result["candidate_pair_count"])
            pair = result["pairs"][0]
            self.assertEqual(
                {".system", "root"},
                {pair["left"]["area"], pair["right"]["area"]},
            )

    def test_cli_command_writes_default_report_and_succeeds_with_findings(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            skills_root = project_root / "agent-skills"
            _write_skill(
                skills_root / "shared-skill" / "SKILL.md",
                name="shared-skill",
                description="Package one local Python CLI with narrow scope.",
                trigger_lines=[
                    "A local Python CLI needs packaging.",
                    "The work should stay narrow and inspectable.",
                ],
                instruction_lines=[
                    "Inspect pyproject.toml and existing entrypoints.",
                    "Prefer small packaging changes over broad rewrites.",
                ],
            )
            _write_skill(
                skills_root / ".system" / "shared-copy" / "SKILL.md",
                name="shared-skill",
                description="Package one local Python CLI with narrow scope.",
                trigger_lines=[
                    "A local Python CLI needs packaging.",
                    "The work should stay narrow and inspectable.",
                ],
                instruction_lines=[
                    "Inspect pyproject.toml and existing entrypoints.",
                    "Prefer small packaging changes over broad rewrites.",
                ],
            )

            original_cwd = Path.cwd()
            stdout = io.StringIO()
            try:
                os.chdir(project_root)
                with patch.object(
                    sys,
                    "argv",
                    [
                        "molt",
                        "skill-builder",
                        "experimental",
                        "find-near-dupe-skills",
                        "--skills-root",
                        "agent-skills",
                    ],
                ):
                    with redirect_stdout(stdout):
                        exit_code = main()
            finally:
                os.chdir(original_cwd)

            payload = json.loads(stdout.getvalue())
            self.assertEqual(0, exit_code)
            self.assertGreater(payload["candidate_pair_count"], 0)
            self.assertTrue(Path(payload["output_path"]).is_file())


def _write_skill(
    skill_path: Path,
    *,
    name: str,
    description: str,
    trigger_lines: list[str],
    instruction_lines: list[str],
) -> None:
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "---",
        f"name: {name}",
        f"description: {description}",
        "---",
        "",
        f"# {name}",
        "",
        "Use this skill when:",
        *[f"- {line}" for line in trigger_lines],
        "",
        "Instructions:",
        *[f"1. {line}" if index == 0 else f"{index + 1}. {line}" for index, line in enumerate(instruction_lines)],
        "",
    ]
    skill_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
