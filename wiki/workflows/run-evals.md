# Run Evals

How Molt runs `eval-skill`, grades results, and interprets benchmark changes.

## Working Guidance
### Stable
- For CLI command skills, pair opt-in flag cases with explicit no-flag cases. Supporting lesson: [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
  Evidence: The existing suite covered `eval-skill ... --baseline snapshot --snapshot-current`, while the new `eval-skill-basic-command` case separately exercised the opposite behavior: do not add snapshot flags when the user asked for a one-off eval.
  Reuse: When a command has optional flags that materially change behavior, add one eval that requires the flag and another that forbids it unless requested.
- Treat `grading.json` entries that say "The grader did not return a result for this check." as grader failures first, not automatic skill regressions. Supporting lesson: [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
  Evidence: In `iteration-2`, the `eval-skill-command` and `eval-skill-basic-command` outputs both contained the expected `./molt skill-builder eval-skill ...` commands and artifact paths in `result.json`, while the corresponding `grading.json` files marked every check failed only because the grader returned no assertions.
  Reuse: When an eval score looks implausibly low, inspect `result.json` alongside `grading.json` before rewriting the skill or the checks, and rerun or simplify the checks if the grader response is empty.
- Artifact-inspection evals should anchor the answer to the target skill workspace, not just to a generic current case directory. Supporting lesson: [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
  Evidence: The `eval-workspace-case-inspection` case asked about `run-summarizer`, but the with-skill output drifted toward the current eval case folder (`iteration-2/eval-eval-workspace-case-inspection/...`) instead of `skills/run-summarizer/evals/workspace/iteration-N/...`.
  Reuse: When authoring skill references or checks for inspection prompts, include the target skill name and expected `skills/<skill>/evals/workspace/...` path pattern explicitly so the response stays attached to the intended workspace.
- When a repo-specific dev skill needs exact local commands, encode the command contract and the anti-substitution rules directly in the skill instead of leaving command shape implicit. Supporting lesson: [lessons/2026-03-28-python-test-coverage-loop-skill.md](../../lessons/2026-03-28-python-test-coverage-loop-skill.md)
  Evidence: `iteration-1` tied on the installed and ad hoc command cases because the with-skill answers drifted to `--cov=.` or omitted `tests`, but `iteration-2` flipped both cases to full wins after the skill and checklist named the exact `python -m pytest tests` and `uv run --with ... --cov=moltfarm` commands and explicitly forbade `uvx`, bare `pytest`, omitted `tests`, and `--cov=.` substitutions.
  Reuse: When a local repo already has the right command contract, reduce the skill's freedom on that surface and prefer exact command pairs over generalized placeholders.
- Treat all-grader-empty semantic checks as grader failures first, not as immediate evidence that the skill regressed. Supporting lesson: [lessons/2026-03-28-python-test-coverage-loop-skill.md](../../lessons/2026-03-28-python-test-coverage-loop-skill.md)
  Evidence: In `iteration-2`, the `eval-lightweight-cli-test-pattern` with-skill output still described lazy imports, parser or help tests, and zero-findings artifact success, but `grading.json` marked every non-trigger check failed only because each one said `The grader did not return a result for this check.`
  Reuse: When an eval case suddenly collapses to trigger-only credit, inspect `result.json` alongside `grading.json` before revising the skill or the eval suite.
- Imported upstream skills should be kept twice: once as untouched storage, once as uniquely named local eval copies. Supporting lesson: [lessons/2026-03-28-python-testing-skill-bakeoff.md](../../lessons/2026-03-28-python-testing-skill-bakeoff.md)
  Evidence: The untouched source copies preserved exact upstream content for inspection, while the renamed local copies allowed `molt skill-builder eval-skill` to run all four skills without name collisions.
  Reuse: For future comparisons, stage untouched upstream folders under `example_upstream_skills/` and create minimal local eval copies under `skills/` that only change metadata needed for discovery.
- Before trusting close bake-off margins, audit grading fallback rates caused by exact-text alignment between requested checks and grader output. Supporting lesson: [lessons/2026-03-28-python-testing-skill-bakeoff.md](../../lessons/2026-03-28-python-testing-skill-bakeoff.md)
  Evidence: This bake-off produced many fallback failures, including `12/18` with-skill checks for `wshobson-python-testing-patterns`, which makes small score differences too noisy to overinterpret.
  Reuse: Always pair benchmark deltas with a fallback-check audit, and prioritize evaluator hardening before using narrow score gaps to choose a winner.
- To distinguish a specialist pytest skill from a strong foundation model, eval cases must demand more than generic correctness. Supporting lesson: [lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md](../../lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md)
  Evidence: The six-case suite covered practical pytest patterns well, but after grading was hardened the no-skill baseline still satisfied every case.
  Reuse: Add cases or checks that reward compactness, sharper tool choice, anti-pattern avoidance, or repo-specific precision if the goal is to separate strong skills from a strong general baseline.
- Any leaderboard produced before a grader-behavior change should be treated as historical, not directly comparable to post-fix runs. Supporting lesson: [lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md](../../lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md)
  Evidence: The original upstream pytest bake-off highlighted Luxor and Mindrally, but the post-fix `python-pytest-essentials` run used a materially different grading path and therefore cannot be ranked fairly against those earlier numbers without rerunning them.
  Reuse: After changing grader alignment, rerun the top comparison set or explicitly label the new run as a follow-up on a changed eval surface.
- Recovering paraphrased grader outputs is necessary, but once that recovery is in place, a generic eval suite may stop separating skill quality from baseline capability. Supporting lesson: [lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md](../../lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md)
  Evidence: After hardening grading alignment and rerunning the six-case pytest suite for `python-pytest-essentials`, both the with-skill and without-skill configurations scored a perfect `1.0` weighted pass rate across all six cases.
  Reuse: When a suite suddenly becomes all ties after a grader fix, treat that as evidence that the suite is saturated, not that every skill is equally good.

### Tentative
- Small text-only skills are sufficient to validate a local model’s practical skill path before attempting full eval loops or local grading. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: Both direct and proxy-backed subject runs showed `function_call:activate_skill:*` and `function_call:read_skill_resource:*` for `repo-triage`, `run-summarizer`, and `docker-smoke-test`, while full local grading remained out of scope.
  Reuse: Start local-model validation with narrow text-only skills and judge success from trace artifacts first; do not block the pilot on local evaluator grading.
- Invalid local grader payloads should downgrade the affected checks to failed grading instead of aborting the whole eval iteration. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: After normalizing alternate summary keys and adding an error fallback in `packages/moltfarm/skill_evaluator.py`, the local `llm-wiki-validator` suite completed and wrote `benchmark.json`, `feedback.json`, and per-case `comparison.json` even though local grader outputs still varied in shape.
  Reuse: When local models are part of the grading path, preserve inspectable iteration artifacts by turning malformed grader output into explicit failed assertions rather than a fatal exception.
- A local `openai_compatible` model can drive subject runs, but full `eval-skill` still needs a grader that emits the repo's exact `GradingPayload` summary schema or a normalization layer in front of it. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: Local Gemma completed subject outputs for both new skills, but both `eval-skill` runs failed when the local grader returned JSON without `summary.passed`, `summary.failed`, `summary.total`, and `summary.pass_rate`.
  Reuse: Keep a cloud grader or add schema normalization before claiming a fully local `eval-skill` loop.
- Wiki-building skills should require page-level update plans to name the exact supporting note, reference, or errata path for each non-obvious fact. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: The partial local grading trace for `llm-wiki` passed the routing and structure checks but missed the evidence-linking check because the plan named the destination pages without explicitly tying each step back to the raw-fragment source.
  Reuse: When a skill proposes wiki updates, require the destination page and supporting source path in the same step so evidence discipline survives summarization.

## Relevant Runtime Surfaces
- [packages/moltfarm/skill_evaluator.py](../../packages/moltfarm/skill_evaluator.py)
- [README.md](../../README.md)
- [skills/molt-cli/SKILL.md](../../skills/molt-cli/SKILL.md)
- [skills/molt-cli/evals/evals.json](../../skills/molt-cli/evals/evals.json)
- [skills/molt-cli/evals/workspace/iteration-2/benchmark.json](../../skills/molt-cli/evals/workspace/iteration-2/benchmark.json)
- [skills/python-test-coverage-loop/SKILL.md](../../skills/python-test-coverage-loop/SKILL.md)
- [skills/python-test-coverage-loop/evals/evals.json](../../skills/python-test-coverage-loop/evals/evals.json)
- [skills/python-test-coverage-loop/evals/workspace/iteration-1/benchmark.json](../../skills/python-test-coverage-loop/evals/workspace/iteration-1/benchmark.json)

## Supporting Lesson Files
- [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
- [lessons/2026-03-28-python-test-coverage-loop-skill.md](../../lessons/2026-03-28-python-test-coverage-loop-skill.md)
- [lessons/2026-03-28-python-testing-skill-bakeoff.md](../../lessons/2026-03-28-python-testing-skill-bakeoff.md)
- [lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md](../../lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md)
- [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
- [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
