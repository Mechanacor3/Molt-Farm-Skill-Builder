# Molt CLI Patterns

## Common commands

- Run an operation:
  - `./molt skill-builder run manual-triage --input target=.`
  - `./molt skill-builder run manual-run-summary --input run_record_path=runs/<run-id>.json`
  - `./molt skill-builder run manual-lesson-extraction --input source_path=runs/<run-id>.json --input comparison_path=runs/<other-run-id>.json`

- Evaluate a skill:
  - `./molt skill-builder eval-skill run-summarizer`
  - `./molt skill-builder eval-skill run-summarizer --baseline snapshot --snapshot-current`

## What to inspect after running

- Operation runs:
  - `runs/<run-id>.json`
  - `logs/YYYY-MM-DD/<run-id>.log`

- Skill evals:
  - `skills/<skill>/evals/workspace/iteration-N/benchmark.json`
  - `skills/<skill>/evals/workspace/iteration-N/feedback.json`
  - `skills/<skill>/evals/workspace/iteration-N/eval-<case-id>/comparison.json`
  - `skills/<skill>/evals/workspace/iteration-N/eval-<case-id>/with_skill/`
  - `skills/<skill>/evals/workspace/iteration-N/eval-<case-id>/without_skill/`
  - `skills/<skill>/evals/workspace/iteration-N/eval-<case-id>/old_skill/`

## Heuristics

- Start with the smallest operation or eval that answers the question.
- Prefer inspecting artifacts already on disk before rerunning expensive commands.
- When a run fails, read the run record and log before editing code.
- When evaluating a skill, compare `with_skill` against the baseline with `comparison.json` and task-uplift metrics before changing `SKILL.md`.
