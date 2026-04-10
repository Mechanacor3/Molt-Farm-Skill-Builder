# Author Skill

How Molt turns a repo need into a portable local skill with inspectable instructions.

## Working Guidance
### Stable
- Refine a skill by rerunning the same concrete input before and after the edit, then compare output shape and evidence handling. Supporting lesson: [lessons/2026-03-20-run-summarizer-refinement.md](../../lessons/2026-03-20-run-summarizer-refinement.md)
  Evidence: The same target run `runs/run-20260320191724-fff0f529.json` produced a looser first summary and a tighter revised summary after only the skill instructions changed.
  Reuse: When improving a skill, keep the test case fixed, change only the skill, and compare the two outputs before promoting the lesson.
- When exposing repo-local skills to Codex, install the repo-shaped set rather than every local skill indiscriminately. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The local Codex skill install kept `molt-cli`, `eval-author`, `lesson-extractor`, `repo-triage`, `run-summarizer`, `skill-finder`, `skill-refiner`, `python-build`, and `docker-smoke-test`, while leaving game-specific skills out of the default set.
  Reuse: Treat Codex local skill installation as part of repo ergonomics; pick the subset that matches the repo’s actual workflow and avoid unrelated clusters by default.
- Repo-specific workflow behavior is easier to evolve when the runtime is backed by a local skill artifact rather than hidden prompt text. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The new `eval-author` behavior lives in `skills/eval-author/SKILL.md`, while the runtime module focuses on session lifecycle, probe orchestration, and artifact writing.
  Reuse: When a new capability contains reusable review logic or domain guidance, capture that guidance as a portable skill and keep the runtime layer narrow.
- Artifact-inspection evals should anchor the answer to the target skill workspace, not just to a generic current case directory. Supporting lesson: [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
  Evidence: The `eval-workspace-case-inspection` case asked about `run-summarizer`, but the with-skill output drifted toward the current eval case folder (`iteration-2/eval-eval-workspace-case-inspection/...`) instead of `skills/run-summarizer/evals/workspace/iteration-N/...`.
  Reuse: When authoring skill references or checks for inspection prompts, include the target skill name and expected `skills/<skill>/evals/workspace/...` path pattern explicitly so the response stays attached to the intended workspace.
- A concise, focused pytest skill can compete well against broader encyclopedic skills when the suite asks for practical answer patterns rather than exhaustive documentation. Supporting lesson: [lessons/2026-03-28-python-testing-skill-bakeoff.md](../../lessons/2026-03-28-python-testing-skill-bakeoff.md)
  Evidence: `mindrally-python-testing` slightly outperformed the no-skill baseline and stayed close to Luxor despite being much shorter than Luxor, ECC, or Wshobson.
  Reuse: The next locally-authored pytest skill should bias toward compact, high-signal guidance and concrete activation cues rather than maximal breadth.
- When a local-first module has broad orchestration but many pure helpers, raise coverage primarily with direct helper tests plus a few thin dispatch tests instead of forcing more large end-to-end setups. Supporting lesson: [lessons/2026-03-28-targeted-helper-tests-for-coverage.md](../../lessons/2026-03-28-targeted-helper-tests-for-coverage.md)
  Evidence: Covering CLI dispatch arms directly and testing runner/eval-authoring normalization helpers in isolation moved total coverage from `82%` to `94%` without runtime refactors or broader fixture sprawl.
  Reuse: Prefer small file-backed fixtures and direct helper assertions for validation, normalization, import, and path-handling branches; keep end-to-end tests for only the orchestration seams that actually need them.
- A promoted knowledge index should preserve supporting file paths so authoring and refinement flows can retrieve the right raw lesson even when the lesson prose is generic. Supporting lesson: [lessons/2026-04-09-workflow-first-system-map-from-lessons.md](../../lessons/2026-04-09-workflow-first-system-map-from-lessons.md)
  Evidence: The promoted `wiki/_build/lesson-index.json` now stores `supporting_paths`, and both authoring and refinement lookups consult that index before falling back to raw lesson-file substring matching.
  Reuse: When a curated knowledge layer drives retrieval, store the raw lesson path plus enough structured references to route context without re-reading the whole corpus every time.

### Tentative
- Generated eval authoring should preserve existing canonical cases verbatim and append normalized new cases instead of rewriting the suite wholesale. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The draft builder keeps prior `evals/evals.json` cases, de-duplicates generated case ids with suffixes such as `-2`, and avoids overwriting existing fixture files by renaming generated draft fixtures when needed.
  Reuse: Prefer append-and-normalize behavior for generated eval content unless the user explicitly asks for destructive rewrite semantics.
- Conversational eval creation should write a reviewable draft workspace before it touches canonical `evals/` files. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The implemented `create-evals` flow writes `session.json`, probe outputs, suggested flavors, draft fixtures, and `draft/evals.json` under `skills/<skill>/evals/workspace/create-evals/session-N/`, and only promotes into canonical files on explicit `--promote`.
  Reuse: When adding authoring or refinement flows to this repo, keep the first pass additive and inspectable so the user can review artifacts before promotion.
- Keep CLI imports lazy when parser-only or lightweight experimental commands should work without optional runtime dependencies. Supporting lesson: [lessons/2026-03-28-skill-near-dupe-scanner.md](../../lessons/2026-03-28-skill-near-dupe-scanner.md)
  Evidence: Parser and command tests failed until `cli.py` stopped importing `eval_authoring` and `skill_evaluator` at module import time, because those paths pull in optional packages such as `pydantic`.
  Reuse: Import heavy or optional command handlers inside the `main()` branch that actually executes them so `--help`, parser tests, and unrelated commands stay usable in narrower environments.
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
- [skills/molt-skill-builder-authoring/SKILL.md](../../skills/molt-skill-builder-authoring/SKILL.md)
- [README.md](../../README.md)
- [skills/run-summarizer/SKILL.md](../../skills/run-summarizer/SKILL.md)
- [packages/moltfarm/cli.py](../../packages/moltfarm/cli.py)
- [packages/moltfarm/eval_authoring.py](../../packages/moltfarm/eval_authoring.py)
- [skills/eval-author/SKILL.md](../../skills/eval-author/SKILL.md)
- [skills/molt-cli/SKILL.md](../../skills/molt-cli/SKILL.md)
- [skills/molt-cli/evals/evals.json](../../skills/molt-cli/evals/evals.json)

## Supporting Lesson Files
- [lessons/2026-03-20-run-summarizer-refinement.md](../../lessons/2026-03-20-run-summarizer-refinement.md)
- [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
- [lessons/2026-03-28-molt-cli-evals-refinement.md](../../lessons/2026-03-28-molt-cli-evals-refinement.md)
- [lessons/2026-03-28-python-testing-skill-bakeoff.md](../../lessons/2026-03-28-python-testing-skill-bakeoff.md)
- [lessons/2026-03-28-skill-near-dupe-scanner.md](../../lessons/2026-03-28-skill-near-dupe-scanner.md)
- [lessons/2026-03-28-targeted-helper-tests-for-coverage.md](../../lessons/2026-03-28-targeted-helper-tests-for-coverage.md)
- [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
- [lessons/2026-04-09-workflow-first-system-map-from-lessons.md](../../lessons/2026-04-09-workflow-first-system-map-from-lessons.md)
