# Build Evals

How Molt drafts or authors canonical eval suites and keeps them reviewable before promotion.

## Working Guidance
### Stable
- When exposing repo-local skills to Codex, install the repo-shaped set rather than every local skill indiscriminately. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The local Codex skill install kept `molt-cli`, `eval-author`, `lesson-extractor`, `repo-triage`, `run-summarizer`, `skill-finder`, `skill-refiner`, `python-build`, and `docker-smoke-test`, while leaving game-specific skills out of the default set.
  Reuse: Treat Codex local skill installation as part of repo ergonomics; pick the subset that matches the repo’s actual workflow and avoid unrelated clusters by default.
- Repo-specific workflow behavior is easier to evolve when the runtime is backed by a local skill artifact rather than hidden prompt text. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The new `eval-author` behavior lives in `skills/eval-author/SKILL.md`, while the runtime module focuses on session lifecycle, probe orchestration, and artifact writing.
  Reuse: When a new capability contains reusable review logic or domain guidance, capture that guidance as a portable skill and keep the runtime layer narrow.
- For CLI command skills, pair opt-in flag cases with explicit no-flag cases. Supporting lesson: [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
  Evidence: The existing suite covered `eval-skill ... --baseline snapshot --snapshot-current`, while the new `eval-skill-basic-command` case separately exercised the opposite behavior: do not add snapshot flags when the user asked for a one-off eval.
  Reuse: When a command has optional flags that materially change behavior, add one eval that requires the flag and another that forbids it unless requested.
- Treat all-grader-empty semantic checks as grader failures first, not as immediate evidence that the skill regressed. Supporting lesson: [lessons/2026-03-28-python-test-coverage-loop-skill.md](../../lessons/2026-03-28-python-test-coverage-loop-skill.md)
  Evidence: In `iteration-2`, the `eval-lightweight-cli-test-pattern` with-skill output still described lazy imports, parser or help tests, and zero-findings artifact success, but `grading.json` marked every non-trigger check failed only because each one said `The grader did not return a result for this check.`
  Reuse: When an eval case suddenly collapses to trigger-only credit, inspect `result.json` alongside `grading.json` before revising the skill or the eval suite.
- Recovering paraphrased grader outputs is necessary, but once that recovery is in place, a generic eval suite may stop separating skill quality from baseline capability. Supporting lesson: [lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md](../../lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md)
  Evidence: After hardening grading alignment and rerunning the six-case pytest suite for `python-pytest-essentials`, both the with-skill and without-skill configurations scored a perfect `1.0` weighted pass rate across all six cases.
  Reuse: When a suite suddenly becomes all ties after a grader fix, treat that as evidence that the suite is saturated, not that every skill is equally good.

### Tentative
- Generated eval authoring should preserve existing canonical cases verbatim and append normalized new cases instead of rewriting the suite wholesale. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The draft builder keeps prior `evals/evals.json` cases, de-duplicates generated case ids with suffixes such as `-2`, and avoids overwriting existing fixture files by renaming generated draft fixtures when needed.
  Reuse: Prefer append-and-normalize behavior for generated eval content unless the user explicitly asks for destructive rewrite semantics.
- Conversational eval creation should write a reviewable draft workspace before it touches canonical `evals/` files. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The implemented `create-evals` flow writes `session.json`, probe outputs, suggested flavors, draft fixtures, and `draft/evals.json` under `skills/<skill>/evals/workspace/create-evals/session-N/`, and only promotes into canonical files on explicit `--promote`.
  Reuse: When adding authoring or refinement flows to this repo, keep the first pass additive and inspectable so the user can review artifacts before promotion.
- Invalid local grader payloads should downgrade the affected checks to failed grading instead of aborting the whole eval iteration. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: After normalizing alternate summary keys and adding an error fallback in `packages/moltfarm/skill_evaluator.py`, the local `llm-wiki-validator` suite completed and wrote `benchmark.json`, `feedback.json`, and per-case `comparison.json` even though local grader outputs still varied in shape.
  Reuse: When local models are part of the grading path, preserve inspectable iteration artifacts by turning malformed grader output into explicit failed assertions rather than a fatal exception.
- A local `openai_compatible` model can drive subject runs, but full `eval-skill` still needs a grader that emits the repo's exact `GradingPayload` summary schema or a normalization layer in front of it. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: Local Gemma completed subject outputs for both new skills, but both `eval-skill` runs failed when the local grader returned JSON without `summary.passed`, `summary.failed`, `summary.total`, and `summary.pass_rate`.
  Reuse: Keep a cloud grader or add schema normalization before claiming a fully local `eval-skill` loop.
- New skills still need hand-authored canonical evals as a first-class path because `create-evals` can be blocked by external quota or probe-runtime failures. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: `./molt skill-builder create-evals molt-skill-builder-authoring` wrote a reviewable `session-1` workspace but failed on repeated `429 insufficient_quota`, and its `probe-primary-task` observation also recorded an `OSError: [Errno 36] File name too long` failure in `probe-observations.json`.
  Reuse: Author `SKILL.md`, fixtures, and canonical `evals/evals.json` directly first; treat `create-evals` as an additive drafting aid rather than the only route to a shippable skill.
- Authoring-loop skills need an explicit "short ordered actions and commands" instruction to keep local-model responses operational instead of essay-like. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: The first local subject output for `molt-skill-builder-authoring` got the sequence right but expanded into headings and narrative in `iteration-1/.../outputs/summary.txt`, which led to a follow-up tightening of the skill instructions.
  Reuse: When evals expect concise workflow guidance, tell the skill to answer as a short ordered sequence of actions and commands.
- Wiki-building skills should require page-level update plans to name the exact supporting note, reference, or errata path for each non-obvious fact. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: The partial local grading trace for `llm-wiki` passed the routing and structure checks but missed the evidence-linking check because the plan named the destination pages without explicitly tying each step back to the raw-fragment source.
  Reuse: When a skill proposes wiki updates, require the destination page and supporting source path in the same step so evidence discipline survives summarization.
- Curated knowledge layers should write a reviewable draft workspace before they touch canonical wiki pages or promoted indexes. Supporting lesson: [lessons/2026-04-09-workflow-first-system-map-from-lessons.md](../../lessons/2026-04-09-workflow-first-system-map-from-lessons.md)
  Evidence: The new `manual-system-map-draft` flow writes `plan.md`, candidate pages, and a draft `lesson-index.json` under `wiki/drafts/session-N/`, while promotion is a separate `promote-system-map` step.
  Reuse: When adding a new synthesis surface in Molt, keep the first pass additive and inspectable so raw evidence stays untouched until the curated layer is reviewed.

## Relevant Runtime Surfaces
- [packages/moltfarm/eval_authoring.py](../../packages/moltfarm/eval_authoring.py)
- [README.md](../../README.md)
- [packages/moltfarm/cli.py](../../packages/moltfarm/cli.py)
- [skills/eval-author/SKILL.md](../../skills/eval-author/SKILL.md)
- [skills/molt-cli/SKILL.md](../../skills/molt-cli/SKILL.md)
- [skills/molt-cli/evals/evals.json](../../skills/molt-cli/evals/evals.json)
- [skills/molt-cli/evals/workspace/iteration-2/benchmark.json](../../skills/molt-cli/evals/workspace/iteration-2/benchmark.json)
- [skills/python-test-coverage-loop/SKILL.md](../../skills/python-test-coverage-loop/SKILL.md)

## Supporting Lesson Files
- [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
- [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
- [lessons/2026-03-28-python-test-coverage-loop-skill.md](../../lessons/2026-03-28-python-test-coverage-loop-skill.md)
- [lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md](../../lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md)
- [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
- [lessons/2026-04-09-workflow-first-system-map-from-lessons.md](../../lessons/2026-04-09-workflow-first-system-map-from-lessons.md)
