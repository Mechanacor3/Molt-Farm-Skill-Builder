from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages"))

from moltfarm.skill_loader import discover_skill_records, discover_skills, load_skill

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "upstream_skills"


class SkillLoaderReferenceTests(unittest.TestCase):
    def test_load_skill_expands_local_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "example-skill"
            references_dir = skill_dir / "references"
            references_dir.mkdir(parents=True)
            (references_dir / "details.md").write_text(
                "Useful detail from a local reference.",
                encoding="utf-8",
            )
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: example-skill\n"
                "description: Example skill.\n"
                "---\n\n"
                "Read this: @./references/details.md\n",
                encoding="utf-8",
            )

            skill = load_skill(skill_dir / "SKILL.md")

            self.assertEqual(skill.name, "example-skill")
            self.assertEqual([Path("references/details.md")], skill.referenced_paths)
            self.assertIn("Useful detail from a local reference.", skill.instructions)
            self.assertIn("<referenced-file path=\"references/details.md\">", skill.instructions)

    def test_load_skill_rejects_missing_reference(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skill_dir = Path(temp_dir) / "bad-skill"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                "---\n"
                "name: bad-skill\n"
                "description: Missing reference.\n"
                "---\n\n"
                "Read this: @./references/missing.md\n",
                encoding="utf-8",
            )

            with self.assertRaises(FileNotFoundError):
                load_skill(skill_dir / "SKILL.md")

    def test_discover_skills_finds_nested_openai_style_buckets(self) -> None:
        skills = discover_skills(FIXTURES_DIR / "openai_nested")

        self.assertEqual({"openai-docs", "playwright"}, set(skills))
        self.assertEqual("openai-docs", skills["openai-docs"].name)
        self.assertEqual("playwright", skills["playwright"].name)

    def test_discover_skill_records_preserves_area_metadata_and_duplicate_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skills_root = Path(temp_dir) / "skills"
            _write_skill(
                skills_root / "root-skill" / "SKILL.md",
                name="shared-skill",
                description="Root version.",
            )
            _write_skill(
                skills_root / ".system" / "shared-skill" / "SKILL.md",
                name="shared-skill",
                description="System version.",
            )
            _write_skill(
                skills_root / ".curated" / "curated-skill" / "SKILL.md",
                name="curated-skill",
                description="Curated version.",
            )

            records = discover_skill_records(skills_root)

            self.assertEqual(3, len(records))
            self.assertEqual(
                [".curated", ".system", "root"],
                sorted(record.area for record in records),
            )
            self.assertEqual(
                [
                    Path(".curated/curated-skill/SKILL.md"),
                    Path(".system/shared-skill/SKILL.md"),
                    Path("root-skill/SKILL.md"),
                ],
                sorted(record.relative_path for record in records),
            )
            self.assertEqual(
                ["curated-skill", "shared-skill", "shared-skill"],
                sorted(record.skill.name for record in records),
            )

    def test_discover_skills_ignores_generated_eval_workspace_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            skills_root = Path(temp_dir) / "skills"
            real_skill = skills_root / "sample-skill"
            snapshot_skill = (
                real_skill
                / "evals"
                / "workspace"
                / "iteration-1"
                / "skill-snapshot"
                / "sample-skill"
            )
            real_skill.mkdir(parents=True)
            snapshot_skill.mkdir(parents=True)
            (real_skill / "SKILL.md").write_text(
                "---\nname: sample-skill\ndescription: Real skill.\n---\n\nReal body.\n",
                encoding="utf-8",
            )
            (snapshot_skill / "SKILL.md").write_text(
                "---\nname: sample-skill\ndescription: Snapshot skill.\n---\n\nSnapshot body.\n",
                encoding="utf-8",
            )

            skills = discover_skills(skills_root)

            self.assertEqual({"sample-skill"}, set(skills))
            self.assertEqual(real_skill, skills["sample-skill"].path)

    def test_load_skill_handles_anthropic_style_frontmatter_and_body(self) -> None:
        skill = load_skill(FIXTURES_DIR / "anthropic_internal_comms" / "SKILL.md")

        self.assertEqual("internal-comms", skill.name)
        self.assertIn("internal communications", skill.description)
        self.assertIn("examples/", skill.instructions)
        self.assertEqual([], skill.referenced_paths)

    def test_load_skill_expands_explicit_reference_inline_fixture(self) -> None:
        skill = load_skill(FIXTURES_DIR / "reference_inline" / "SKILL.md")

        self.assertEqual([Path("references/checklist.md")], skill.referenced_paths)
        self.assertIn("<referenced-file path=\"references/checklist.md\">", skill.instructions)
        self.assertIn("keep scope narrow", skill.instructions)

    def test_load_skill_collects_bundled_resources_structurally(self) -> None:
        skill = load_skill(FIXTURES_DIR / "resource_bundle" / "SKILL.md")

        self.assertEqual(
            [Path("references/guide.md")],
            skill.resources.references,
        )
        self.assertEqual(
            [Path("scripts/run.py"), Path("scripts/nested/tool.py")],
            skill.resources.scripts,
        )
        self.assertEqual([Path("assets/icon.svg")], skill.resources.assets)
        self.assertEqual([Path("examples/example.md")], skill.resources.examples)
        self.assertEqual([Path("agents/helper.yaml")], skill.resources.agents)
        self.assertEqual([Path("LICENSE.txt")], skill.resources.other)
        wrapped = skill.resources.as_wrapped_block()
        self.assertIn('<skill_resources>', wrapped)
        self.assertIn('<file category="scripts">scripts/run.py</file>', wrapped)
        self.assertIn('<file category="references">references/guide.md</file>', wrapped)
        self.assertIn('<file category="other">LICENSE.txt</file>', wrapped)

def _write_skill(skill_path: Path, *, name: str, description: str) -> None:
    skill_path.parent.mkdir(parents=True, exist_ok=True)
    skill_path.write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\nUse it.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
