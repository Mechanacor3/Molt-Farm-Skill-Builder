# Skill Near-Dupe Scanner Lessons

Source:
- feature: `packages/moltfarm/experimental/near_dupe_skills.py`
- discovery helper: `packages/moltfarm/skill_loader.py`
- validation method: targeted unit tests plus a real CLI smoke run against `skills/`
- smoke report: `tmp/manual-near-dupe-report.json`

## Discovery Shape Lesson

- `lesson`: Preserve one record per discovered `SKILL.md` whenever the task is analysis rather than activation.
- `evidence`: Near-dupe detection needed area metadata and duplicate-name preservation, which the existing name-keyed `discover_skills()` map could not provide because it collapses collisions.
- `scope`: skill inventory analysis
- `reuse`: For reporting, diffing, and overlap detection work, start from a list-based discovery helper and only collapse to a dict at the last moment if the caller truly needs unique names.

## CLI Dependency Lesson

- `lesson`: Keep CLI imports lazy when parser-only or lightweight experimental commands should work without optional runtime dependencies.
- `evidence`: Parser and command tests failed until `cli.py` stopped importing `eval_authoring` and `skill_evaluator` at module import time, because those paths pull in optional packages such as `pydantic`.
- `scope`: local CLI design
- `reuse`: Import heavy or optional command handlers inside the `main()` branch that actually executes them so `--help`, parser tests, and unrelated commands stay usable in narrower environments.

## Threshold Discipline Lesson

- `lesson`: Separate “candidate found” from “analysis succeeded” when a conservative heuristic is intentionally allowed to return zero matches.
- `evidence`: The real smoke run over this repo's current `skills/` tree completed successfully and wrote a report, but produced zero pairs because the planned `>= 0.50` threshold stayed conservative.
- `scope`: experimental heuristic analyzers
- `reuse`: For advisory analyzers, always emit an inspectable artifact and a successful exit path even when the current corpus yields no findings, then let threshold tuning happen explicitly in a later refinement.
