# Molt CLI Patterns

## Common commands

- Run a workflow:
  - `./molt run manual-triage --input target=.`
  - `./molt run manual-run-summary --input run_record_path=runs/<run-id>.json`

- Evaluate a skill:
  - `./molt eval-skill run-summarizer`
  - `./molt eval-skill run-summarizer --baseline snapshot --snapshot-current`

## What to inspect after running

- Workflow runs:
  - `runs/<run-id>.json`
  - `logs/YYYY-MM-DD/<run-id>.log`

- Skill evals:
  - `skills/<skill>/evals/workspace/iteration-N/benchmark.json`
  - `skills/<skill>/evals/workspace/iteration-N/feedback.json`
  - `skills/<skill>/evals/workspace/iteration-N/eval-<case-id>/with_skill/`
  - `skills/<skill>/evals/workspace/iteration-N/eval-<case-id>/without_skill/`
  - `skills/<skill>/evals/workspace/iteration-N/eval-<case-id>/old_skill/`

## Heuristics

- Start with the smallest workflow or eval that answers the question.
- Prefer inspecting artifacts already on disk before rerunning expensive commands.
- When a run fails, read the run record and log before editing code.
- When evaluating a skill, compare `with_skill` against the baseline before changing `SKILL.md`.
