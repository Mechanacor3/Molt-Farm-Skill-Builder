# Skill Brief

Create a new local skill named `schema-diff-review`.

Goal:
- Review a small schema or contract diff and produce concise migration-risk notes for a human engineer.

Constraints:
- Keep the skill local-first and inspectable.
- Prefer one `SKILL.md`, a small reference if needed, and realistic local eval fixtures.
- Do not add runtime code unless the same logic would otherwise be rewritten repeatedly.

Success:
- The skill has a narrow authoring surface.
- The skill gets a canonical eval suite.
- The author can inspect local artifacts, capture lessons, refine, and rerun.
