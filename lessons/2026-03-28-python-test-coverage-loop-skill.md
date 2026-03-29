# Python Test Coverage Loop Skill Lessons

Source:
- skill: `skills/python-test-coverage-loop/SKILL.md`
- reference: `skills/python-test-coverage-loop/references/repo-test-coverage-checklist.md`
- eval suite: `skills/python-test-coverage-loop/evals/evals.json`
- validation method: `./molt skill-builder eval-skill python-test-coverage-loop`
- benchmark snapshots:
  - `skills/python-test-coverage-loop/evals/workspace/iteration-1/benchmark.json`
  - `skills/python-test-coverage-loop/evals/workspace/iteration-2/benchmark.json`

## Command Contract Lesson

- `lesson`: When a repo-specific dev skill needs exact local commands, encode the command contract and the anti-substitution rules directly in the skill instead of leaving command shape implicit.
- `evidence`: `iteration-1` tied on the installed and ad hoc command cases because the with-skill answers drifted to `--cov=.` or omitted `tests`, but `iteration-2` flipped both cases to full wins after the skill and checklist named the exact `python -m pytest tests` and `uv run --with ... --cov=moltfarm` commands and explicitly forbade `uvx`, bare `pytest`, omitted `tests`, and `--cov=.` substitutions.
- `scope`: repo-specific command skills
- `reuse`: When a local repo already has the right command contract, reduce the skill's freedom on that surface and prefer exact command pairs over generalized placeholders.

## Eval Interpretation Lesson

- `lesson`: Treat all-grader-empty semantic checks as grader failures first, not as immediate evidence that the skill regressed.
- `evidence`: In `iteration-2`, the `eval-lightweight-cli-test-pattern` with-skill output still described lazy imports, parser or help tests, and zero-findings artifact success, but `grading.json` marked every non-trigger check failed only because each one said `The grader did not return a result for this check.`
- `scope`: Molt skill eval review
- `reuse`: When an eval case suddenly collapses to trigger-only credit, inspect `result.json` alongside `grading.json` before revising the skill or the eval suite.
