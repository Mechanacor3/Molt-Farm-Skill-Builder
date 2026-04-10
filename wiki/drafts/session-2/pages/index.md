# Molt System Map

Workflow-first guide to the current Molt loop, built from durable lesson files.

## Primary Workflows
- [Author Skill](workflows/author-skill.md): How Molt turns a repo need into a portable local skill with inspectable instructions. (5 lesson items)
- [Build Evals](workflows/build-evals.md): How Molt drafts or authors canonical eval suites and keeps them reviewable before promotion. (5 lesson items)
- [Run Evals](workflows/run-evals.md): How Molt runs `eval-skill`, grades results, and interprets benchmark changes. (4 lesson items)
- [Inspect Artifacts](workflows/inspect-artifacts.md): How Molt treats runs, logs, traces, and workspace files as the source of truth for review. (6 lesson items)
- [Extract Lessons](workflows/extract-lessons.md): How Molt distills run and eval evidence into reusable lesson files. (12 lesson items)
- [Refine And Rerun](workflows/refine-and-rerun.md): How Molt applies lessons back into skills, reruns the same surface, and checks whether behavior improved. (0 lesson items)
- [Local Model Pilot](workflows/local-model-pilot.md): How Molt validates a direct local-model path first, then layers proxy-backed surfaces and local grading carefully. (8 lesson items)

## Components
- [CLI And Operations](components/cli-and-operations.md): The small CLI and named operation layer that exposes Molt workflows. (9 lesson items)
- [Evaluator And Grading](components/evaluator-and-grading.md): The evaluator, grader contracts, and benchmark interpretation rules. (6 lesson items)
- [Local Model Proxy](components/local-model-proxy.md): The direct local-model path and the proxy-backed Responses compatibility layer. (7 lesson items)
- [Testing And Evidence](components/testing-and-evidence.md): How tests, traces, and file-backed artifacts validate changes without hiding the evidence. (7 lesson items)
- [Wiki Authoring](components/wiki-authoring.md): The evidence discipline and taxonomy rules for turning notes into curated wiki pages. (5 lesson items)

## Raw Lesson Files
- Source corpus size: 3 files / 12 lesson items
- [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
- [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
- [lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md](../../../../lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md)

## Promotion Model
- Draft sessions live under `wiki/drafts/session-N/` and stay reviewable until promotion.
- Promotion refreshes `wiki/_build/lesson-index.json` without rewriting raw lesson files.
