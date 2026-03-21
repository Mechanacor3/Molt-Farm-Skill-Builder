---
name: molt-cli
description: Use the Molt Farm CLI to run workflows, evaluate skills, and inspect the resulting run, log, lesson, and eval artifacts. Use when working inside this repo and the task is about operating `./molt` rather than editing runtime code directly.
---

# Molt CLI

Use this skill when:
- You need to run a workflow with `./molt run`.
- You need to evaluate a skill with `./molt eval-skill`.
- You need to inspect the artifacts produced by the Molt CLI inside this repository.

Instructions:
1. Treat `./molt` as the main local control surface for this repo.
2. Prefer narrow inputs with `--input key=value`. Do not pass broad repo context unless the task clearly requires it.
3. For workflow execution, start with `./molt run <workflow-name>` and add only the smallest necessary overrides.
4. For skill evaluation, use `./molt eval-skill <skill-name>` and inspect the iteration workspace it creates.
5. After any CLI action, inspect the generated artifacts instead of guessing:
   - `runs/` for structured run records
   - `logs/YYYY-MM-DD/` for append-only summaries
   - `lessons/` for distilled lessons
   - `skills/<skill>/evals/workspace/` for eval outputs
6. When the command shape or artifact paths matter, use `@./references/command-patterns.md`.
7. Stay in CLI-operator mode. If the user asks to change runtime behavior, switch to the relevant repo skill or edit code directly.
