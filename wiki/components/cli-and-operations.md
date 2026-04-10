# CLI And Operations

The small CLI and named operation layer that exposes Molt workflows.

## Working Guidance
### Stable
- Always include a dedicated gaps field that lists unperformed verifications and unconfirmed assumptions. Supporting lesson: [lessons/2026-03-20-run-summarizer-refinement.md](../../lessons/2026-03-20-run-summarizer-refinement.md)
  Evidence: The revised summary adds `gaps: No live build or import/CLI verification; existence of packages/moltfarm/cli.py was not confirmed.` while the initial summary had no explicit gaps field.
  Reuse: Require a `gaps` field in summary-style skills whenever the run may leave important checks unperformed.
- Distinguish stdout-only checks from artifact-writing checks explicitly in the output contract. Supporting lesson: [lessons/2026-03-21-docker-smoke-test-refinement.md](../../lessons/2026-03-21-docker-smoke-test-refinement.md)
  Evidence: The repo validation had two different container patterns: CLI help and `unittest` runs were stdout-first, while bind-mounted workflow runs were artifact-first and needed a host path to inspect.
  Reuse: In Docker test recommendations, tell the user whether the post-run inspection target is `stdout` or a host path, and only add a bind mount when the latter is needed.
- When exposing repo-local skills to Codex, install the repo-shaped set rather than every local skill indiscriminately. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The local Codex skill install kept `molt-cli`, `eval-author`, `lesson-extractor`, `repo-triage`, `run-summarizer`, `skill-finder`, `skill-refiner`, `python-build`, and `docker-smoke-test`, while leaving game-specific skills out of the default set.
  Reuse: Treat Codex local skill installation as part of repo ergonomics; pick the subset that matches the repo’s actual workflow and avoid unrelated clusters by default.
- Repo-specific workflow behavior is easier to evolve when the runtime is backed by a local skill artifact rather than hidden prompt text. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The new `eval-author` behavior lives in `skills/eval-author/SKILL.md`, while the runtime module focuses on session lifecycle, probe orchestration, and artifact writing.
  Reuse: When a new capability contains reusable review logic or domain guidance, capture that guidance as a portable skill and keep the runtime layer narrow.
- For CLI command skills, pair opt-in flag cases with explicit no-flag cases. Supporting lesson: [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
  Evidence: The existing suite covered `eval-skill ... --baseline snapshot --snapshot-current`, while the new `eval-skill-basic-command` case separately exercised the opposite behavior: do not add snapshot flags when the user asked for a one-off eval.
  Reuse: When a command has optional flags that materially change behavior, add one eval that requires the flag and another that forbids it unless requested.
- Treat `grading.json` entries that say "The grader did not return a result for this check." as grader failures first, not automatic skill regressions. Supporting lesson: [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
  Evidence: In `iteration-2`, the `eval-skill-command` and `eval-skill-basic-command` outputs both contained the expected `./molt skill-builder eval-skill ...` commands and artifact paths in `result.json`, while the corresponding `grading.json` files marked every check failed only because the grader returned no assertions.
  Reuse: When an eval score looks implausibly low, inspect `result.json` alongside `grading.json` before rewriting the skill or the checks, and rerun or simplify the checks if the grader response is empty.
- Artifact-inspection evals should anchor the answer to the target skill workspace, not just to a generic current case directory. Supporting lesson: [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
  Evidence: The `eval-workspace-case-inspection` case asked about `run-summarizer`, but the with-skill output drifted toward the current eval case folder (`iteration-2/eval-eval-workspace-case-inspection/...`) instead of `skills/run-summarizer/evals/workspace/iteration-N/...`.
  Reuse: When authoring skill references or checks for inspection prompts, include the target skill name and expected `skills/<skill>/evals/workspace/...` path pattern explicitly so the response stays attached to the intended workspace.
- Put stable test discovery and coverage defaults in `pyproject.toml` so local commands stay short and predictable. Supporting lesson: [lessons/2026-03-28-python-test-and-coverage-entrypoints.md](../../lessons/2026-03-28-python-test-and-coverage-entrypoints.md)
  Evidence: `tool.pytest.ini_options` now anchors collection to `tests/`, and `tool.coverage.*` defines `moltfarm` as the measured source with missing-line reporting enabled.
  Reuse: Prefer repo-local configuration over ad hoc shell flags when the goal is repeatable test and coverage behavior for every contributor.
- Keep local Python test tooling behind an explicit repo install path instead of assuming `pytest` is globally available. Supporting lesson: [lessons/2026-03-28-python-test-and-coverage-entrypoints.md](../../lessons/2026-03-28-python-test-and-coverage-entrypoints.md)
  Evidence: The repo now exposes a `test` extra with `pytest` and `pytest-cov`, while the README also preserves ad hoc `uv run --with ...` commands for one-off runs.
  Reuse: When a repo depends on non-runtime Python tools, expose them through a named extra or similarly explicit install path and document the exact command that uses them.
- When a repo-specific dev skill needs exact local commands, encode the command contract and the anti-substitution rules directly in the skill instead of leaving command shape implicit. Supporting lesson: [lessons/2026-03-28-python-test-coverage-loop-skill.md](../../lessons/2026-03-28-python-test-coverage-loop-skill.md)
  Evidence: `iteration-1` tied on the installed and ad hoc command cases because the with-skill answers drifted to `--cov=.` or omitted `tests`, but `iteration-2` flipped both cases to full wins after the skill and checklist named the exact `python -m pytest tests` and `uv run --with ... --cov=moltfarm` commands and explicitly forbade `uvx`, bare `pytest`, omitted `tests`, and `--cov=.` substitutions.
  Reuse: When a local repo already has the right command contract, reduce the skill's freedom on that surface and prefer exact command pairs over generalized placeholders.
- Treat all-grader-empty semantic checks as grader failures first, not as immediate evidence that the skill regressed. Supporting lesson: [lessons/2026-03-28-python-test-coverage-loop-skill.md](../../lessons/2026-03-28-python-test-coverage-loop-skill.md)
  Evidence: In `iteration-2`, the `eval-lightweight-cli-test-pattern` with-skill output still described lazy imports, parser or help tests, and zero-findings artifact success, but `grading.json` marked every non-trigger check failed only because each one said `The grader did not return a result for this check.`
  Reuse: When an eval case suddenly collapses to trigger-only credit, inspect `result.json` alongside `grading.json` before revising the skill or the eval suite.
- Imported upstream skills should be kept twice: once as untouched storage, once as uniquely named local eval copies. Supporting lesson: [lessons/2026-03-28-python-testing-skill-bakeoff.md](../../lessons/2026-03-28-python-testing-skill-bakeoff.md)
  Evidence: The untouched source copies preserved exact upstream content for inspection, while the renamed local copies allowed `molt skill-builder eval-skill` to run all four skills without name collisions.
  Reuse: For future comparisons, stage untouched upstream folders under `example_upstream_skills/` and create minimal local eval copies under `skills/` that only change metadata needed for discovery.
- When a local-first module has broad orchestration but many pure helpers, raise coverage primarily with direct helper tests plus a few thin dispatch tests instead of forcing more large end-to-end setups. Supporting lesson: [lessons/2026-03-28-targeted-helper-tests-for-coverage.md](../../lessons/2026-03-28-targeted-helper-tests-for-coverage.md)
  Evidence: Covering CLI dispatch arms directly and testing runner/eval-authoring normalization helpers in isolation moved total coverage from `82%` to `94%` without runtime refactors or broader fixture sprawl.
  Reuse: Prefer small file-backed fixtures and direct helper assertions for validation, normalization, import, and path-handling branches; keep end-to-end tests for only the orchestration seams that actually need them.
- A promoted knowledge index should preserve supporting file paths so authoring and refinement flows can retrieve the right raw lesson even when the lesson prose is generic. Supporting lesson: [lessons/2026-04-09-workflow-first-system-map-from-lessons.md](../../lessons/2026-04-09-workflow-first-system-map-from-lessons.md)
  Evidence: The promoted `wiki/_build/lesson-index.json` now stores `supporting_paths`, and both authoring and refinement lookups consult that index before falling back to raw lesson-file substring matching.
  Reuse: When a curated knowledge layer drives retrieval, store the raw lesson path plus enough structured references to route context without re-reading the whole corpus every time.

### Tentative
- Preserve source order exactly when one command references multiple skills. Supporting lesson: [lessons/2026-03-28-codex-skill-system-harness.md](../../lessons/2026-03-28-codex-skill-system-harness.md)
  Evidence: The `gamelab-autotrigger` case only became meaningful once the analyzer emitted `develop-web-game` and then `playwright` from a single shell command in left-to-right order.
  Reuse: When multiple evidence hits come from one command or record, emit them in source order instead of collapsing or re-sorting them.
- Generated eval authoring should preserve existing canonical cases verbatim and append normalized new cases instead of rewriting the suite wholesale. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The draft builder keeps prior `evals/evals.json` cases, de-duplicates generated case ids with suffixes such as `-2`, and avoids overwriting existing fixture files by renaming generated draft fixtures when needed.
  Reuse: Prefer append-and-normalize behavior for generated eval content unless the user explicitly asks for destructive rewrite semantics.
- Conversational eval creation should write a reviewable draft workspace before it touches canonical `evals/` files. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The implemented `create-evals` flow writes `session.json`, probe outputs, suggested flavors, draft fixtures, and `draft/evals.json` under `skills/<skill>/evals/workspace/create-evals/session-N/`, and only promotes into canonical files on explicit `--promote`.
  Reuse: When adding authoring or refinement flows to this repo, keep the first pass additive and inspectable so the user can review artifacts before promotion.
- Keep CLI imports lazy when parser-only or lightweight experimental commands should work without optional runtime dependencies. Supporting lesson: [lessons/2026-03-28-skill-near-dupe-scanner.md](../../lessons/2026-03-28-skill-near-dupe-scanner.md)
  Evidence: Parser and command tests failed until `cli.py` stopped importing `eval_authoring` and `skill_evaluator` at module import time, because those paths pull in optional packages such as `pydantic`.
  Reuse: Import heavy or optional command handlers inside the `main()` branch that actually executes them so `--help`, parser tests, and unrelated commands stay usable in narrower environments.
- Small text-only skills are sufficient to validate a local model’s practical skill path before attempting full eval loops or local grading. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: Both direct and proxy-backed subject runs showed `function_call:activate_skill:*` and `function_call:read_skill_resource:*` for `repo-triage`, `run-summarizer`, and `docker-smoke-test`, while full local grading remained out of scope.
  Reuse: Start local-model validation with narrow text-only skills and judge success from trace artifacts first; do not block the pilot on local evaluator grading.
- For a local-model pilot, make direct chat-completions the baseline path and treat proxy-backed Responses as a second surface. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: Gemma worked immediately on the direct `llama.cpp` surface for `get_weather`, the full `exec_command` capability probe, and the three basic skill runs, while the proxy path required additional compatibility fixes before the same workflows passed.
  Reuse: When adding a new local backend, prove the direct OpenAI-compatible chat path first, then layer a Responses proxy on top only after tool calling is already known-good.
- A local Responses proxy must handle authenticated upstreams explicitly and expose the health contract the caller expects. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: The first proxy attempts failed until the proxy accepted `MOLT_UPSTREAM_API_KEY`, forwarded upstream auth, and exposed `/health` in addition to `/healthz`, while the runtime also had to treat `GET /v1/responses` returning `405` as a healthy Responses preflight.
  Reuse: When fronting an authenticated local model server, wire explicit upstream auth and support both health aliases before debugging higher-level tool behavior.
- The OpenAI Responses client may send message items as plain `{"role": ..., "content": ...}` objects inside list input, so a proxy cannot assume every item has an explicit `"type"`. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: The first real `openai_responses` workflow failed with a proxy `500` because the translator only accepted typed items; normalizing role/content pairs into `type="message"` fixed the failure and allowed the `manual-triage`, `manual-run-summary`, and `manual-docker-smoke-test` workflows to complete.
  Reuse: Accept the SDK-style untyped message shape and convert any remaining input-shape errors into structured `400` responses instead of leaking internal server errors.
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
- [packages/moltfarm/cli.py](../../packages/moltfarm/cli.py)
- [packages/moltfarm/operations.py](../../packages/moltfarm/operations.py)
- [skills/run-summarizer/SKILL.md](../../skills/run-summarizer/SKILL.md)
- [skills/docker-smoke-test/SKILL.md](../../skills/docker-smoke-test/SKILL.md)
- [packages/moltfarm/experimental/codex_corpus.py](../../packages/moltfarm/experimental/codex_corpus.py)
- [packages/moltfarm/experimental/codex_timeline.py](../../packages/moltfarm/experimental/codex_timeline.py)
- [tmp/codex-skill-corpus/20260327-185100-520564/report.json](../../tmp/codex-skill-corpus/20260327-185100-520564/report.json)
- [packages/moltfarm/eval_authoring.py](../../packages/moltfarm/eval_authoring.py)

## Supporting Lesson Files
- [lessons/2026-03-20-run-summarizer-refinement.md](../../lessons/2026-03-20-run-summarizer-refinement.md)
- [lessons/2026-03-21-docker-smoke-test-refinement.md](../../lessons/2026-03-21-docker-smoke-test-refinement.md)
- [lessons/2026-03-28-codex-skill-system-harness.md](../../lessons/2026-03-28-codex-skill-system-harness.md)
- [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
- [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
- [lessons/2026-03-28-python-test-and-coverage-entrypoints.md](../../lessons/2026-03-28-python-test-and-coverage-entrypoints.md)
- [lessons/2026-03-28-python-test-coverage-loop-skill.md](../../lessons/2026-03-28-python-test-coverage-loop-skill.md)
- [lessons/2026-03-28-python-testing-skill-bakeoff.md](../../lessons/2026-03-28-python-testing-skill-bakeoff.md)
- [lessons/2026-03-28-skill-near-dupe-scanner.md](../../lessons/2026-03-28-skill-near-dupe-scanner.md)
- [lessons/2026-03-28-targeted-helper-tests-for-coverage.md](../../lessons/2026-03-28-targeted-helper-tests-for-coverage.md)
- [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
- [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
- [lessons/2026-04-09-workflow-first-system-map-from-lessons.md](../../lessons/2026-04-09-workflow-first-system-map-from-lessons.md)
