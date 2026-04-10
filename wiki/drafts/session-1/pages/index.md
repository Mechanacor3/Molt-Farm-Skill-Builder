# Molt System Map

Workflow-first guide to the current Molt loop, built from durable lesson files.

## Primary Workflows
- [Author Skill](workflows/author-skill.md): How Molt turns a repo need into a portable local skill with inspectable instructions. (16 lesson items)
- [Build Evals](workflows/build-evals.md): How Molt drafts or authors canonical eval suites and keeps them reviewable before promotion. (13 lesson items)
- [Run Evals](workflows/run-evals.md): How Molt runs `eval-skill`, grades results, and interprets benchmark changes. (14 lesson items)
- [Inspect Artifacts](workflows/inspect-artifacts.md): How Molt treats runs, logs, traces, and workspace files as the source of truth for review. (24 lesson items)
- [Extract Lessons](workflows/extract-lessons.md): How Molt distills run and eval evidence into reusable lesson files. (48 lesson items)
- [Refine And Rerun](workflows/refine-and-rerun.md): How Molt applies lessons back into skills, reruns the same surface, and checks whether behavior improved. (20 lesson items)
- [Local Model Pilot](workflows/local-model-pilot.md): How Molt validates a direct local-model path first, then layers proxy-backed surfaces and local grading carefully. (7 lesson items)

## Components
- [CLI And Operations](components/cli-and-operations.md): The small CLI and named operation layer that exposes Molt workflows. (28 lesson items)
- [Evaluator And Grading](components/evaluator-and-grading.md): The evaluator, grader contracts, and benchmark interpretation rules. (16 lesson items)
- [Local Model Proxy](components/local-model-proxy.md): The direct local-model path and the proxy-backed Responses compatibility layer. (6 lesson items)
- [Skill Instructions](components/skill-instructions.md): The portable `SKILL.md` layer where repo-specific guidance should live. (3 lesson items)
- [Testing And Evidence](components/testing-and-evidence.md): How tests, traces, and file-backed artifacts validate changes without hiding the evidence. (34 lesson items)
- [Wiki Authoring](components/wiki-authoring.md): The evidence discipline and taxonomy rules for turning notes into curated wiki pages. (7 lesson items)

## Raw Lesson Files
- Source corpus size: 14 files / 48 lesson items
- [lessons/2026-03-20-run-summarizer-refinement.md](../../../../lessons/2026-03-20-run-summarizer-refinement.md)
- [lessons/2026-03-21-docker-smoke-test-refinement.md](../../../../lessons/2026-03-21-docker-smoke-test-refinement.md)
- [lessons/2026-03-28-codex-skill-system-harness.md](../../../../lessons/2026-03-28-codex-skill-system-harness.md)
- [lessons/2026-03-28-conversational-eval-authoring.md](../../../../lessons/2026-03-28-conversational-eval-authoring.md)
- [lessons/2026-03-28-molt-cli-evals-refinement.md](../../../../lessons/2026-03-28-molt-cli-evals-refinement.md)
- [lessons/2026-03-28-python-test-and-coverage-entrypoints.md](../../../../lessons/2026-03-28-python-test-and-coverage-entrypoints.md)
- [lessons/2026-03-28-python-test-coverage-loop-skill.md](../../../../lessons/2026-03-28-python-test-coverage-loop-skill.md)
- [lessons/2026-03-28-python-testing-skill-bakeoff.md](../../../../lessons/2026-03-28-python-testing-skill-bakeoff.md)
- [lessons/2026-03-28-skill-near-dupe-scanner.md](../../../../lessons/2026-03-28-skill-near-dupe-scanner.md)
- [lessons/2026-03-28-targeted-helper-tests-for-coverage.md](../../../../lessons/2026-03-28-targeted-helper-tests-for-coverage.md)
- [lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md](../../../../lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md)
- [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)

## Promotion Model
- Draft sessions live under `wiki/drafts/session-N/` and stay reviewable until promotion.
- Promotion refreshes `wiki/_build/lesson-index.json` without rewriting raw lesson files.
