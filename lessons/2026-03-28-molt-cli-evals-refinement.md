# Molt CLI Evals Refinement Lessons

Source:
- skill: `skills/molt-cli/SKILL.md`
- eval suite: `skills/molt-cli/evals/evals.json`
- validation method: `./molt skill-builder eval-skill molt-cli`
- benchmark: `skills/molt-cli/evals/workspace/iteration-2/benchmark.json`

## Grader Fallback Lesson

- `lesson`: Treat `grading.json` entries that say "The grader did not return a result for this check." as grader failures first, not automatic skill regressions.
- `evidence`: In `iteration-2`, the `eval-skill-command` and `eval-skill-basic-command` outputs both contained the expected `./molt skill-builder eval-skill ...` commands and artifact paths in `result.json`, while the corresponding `grading.json` files marked every check failed only because the grader returned no assertions.
- `scope`: command-oriented skill evals that rely on the LLM grader
- `reuse`: When an eval score looks implausibly low, inspect `result.json` alongside `grading.json` before rewriting the skill or the checks, and rerun or simplify the checks if the grader response is empty.

## Target Workspace Lesson

- `lesson`: Artifact-inspection evals should anchor the answer to the target skill workspace, not just to a generic current case directory.
- `evidence`: The `eval-workspace-case-inspection` case asked about `run-summarizer`, but the with-skill output drifted toward the current eval case folder (`iteration-2/eval-eval-workspace-case-inspection/...`) instead of `skills/run-summarizer/evals/workspace/iteration-N/...`.
- `scope`: skills that tell users where to inspect local eval artifacts
- `reuse`: When authoring skill references or checks for inspection prompts, include the target skill name and expected `skills/<skill>/evals/workspace/...` path pattern explicitly so the response stays attached to the intended workspace.

## Flag Pairing Lesson

- `lesson`: For CLI command skills, pair opt-in flag cases with explicit no-flag cases.
- `evidence`: The existing suite covered `eval-skill ... --baseline snapshot --snapshot-current`, while the new `eval-skill-basic-command` case separately exercised the opposite behavior: do not add snapshot flags when the user asked for a one-off eval.
- `scope`: command-form skill eval suites
- `reuse`: When a command has optional flags that materially change behavior, add one eval that requires the flag and another that forbids it unless requested.
