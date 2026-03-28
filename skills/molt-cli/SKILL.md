---
name: molt-cli
description: Use the Molt Farm Skill Builder CLI to run named skill-builder operations, evaluate skills, and inspect the resulting run, log, lesson, and eval artifacts. Use when working inside this repo and the task is about operating `./molt skill-builder ...` rather than editing runtime code directly.
---

# Molt CLI

Use this skill when:
- You need to run a named skill-builder operation with `./molt skill-builder run`.
- You need to evaluate a skill with `./molt skill-builder eval-skill`.
- You need to inspect the artifacts produced by the Molt CLI inside this repository.

Instructions:
1. Treat `./molt skill-builder ...` as the main local control surface for this repo.
2. Prefer narrow inputs with `--input key=value`. Do not pass broad repo context unless the task clearly requires it.
3. For operation execution, start with `./molt skill-builder run <operation-name>` and add only the smallest necessary overrides.
4. For skill evaluation, use `./molt skill-builder eval-skill <skill-name>` and inspect the iteration workspace it creates.
5. After any CLI action, inspect the generated artifacts instead of guessing:
   - `runs/` for structured run records
   - `logs/YYYY-MM-DD/` for append-only summaries
   - `lessons/` for distilled lessons
   - `skills/<skill>/evals/workspace/` for eval outputs, including `comparison.json` and `benchmark.json`
6. When the command shape or artifact paths matter, use `@./references/command-patterns.md`.
7. Stay in skill-builder CLI mode. If the user asks to change runtime behavior, switch to the relevant repo skill or edit code directly.
