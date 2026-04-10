---
name: molt-skill-builder-authoring
description: Guide contributors through authoring, evaluating, and refining a local Molt Farm skill using the repo's create-evals, eval-skill, artifact inspection, lesson capture, and rerun loop. Use when building or improving a skill in this repo rather than just asking for one exact command.
---

# Molt Skill Builder Authoring

Use this skill when:
- You are creating a new skill under `skills/` in this repo.
- You are refining an existing Molt Farm skill from eval evidence, lessons, or workspace artifacts.
- You need the full local authoring loop, not just one exact `./molt` command.

Instructions:
1. Start with the smallest authoring surface that fits the task: `SKILL.md`, only the needed `references/`, `scripts/`, `assets/`, `evals/`, and `agents/openai.yaml`.
2. Keep the skill distinct from nearby skills. If a request is only about exact CLI syntax or artifact paths, use `molt-cli` instead of broadening this skill.
3. Default authoring loop:
   - write or tighten `SKILL.md`
   - add only the smallest supporting references or fixtures
   - draft or extend evals with `./molt skill-builder create-evals <skill>`
   - review the draft session workspace before promotion
   - promote the accepted draft into canonical `evals/`
   - run `./molt skill-builder eval-skill <skill>`
   - inspect `benchmark.json`, `feedback.json`, and per-case `comparison.json`
   - capture the best lesson, refine narrowly, and rerun
4. When using `create-evals`, prefer small, realistic, additive cases. Keep fixtures plain and skill-local under `evals/files/`.
5. Before editing a skill after an eval, inspect the strongest local evidence first: benchmark summary, feedback, one or two failing case comparisons, and the matching `with_skill/` versus `without_skill/` outputs.
6. Promote lessons only when they change future authoring behavior. Keep them concrete and attributable to an observed failure mode or improvement.
7. Keep the repo local-first: narrow inputs, inspectable files, no broad repo dumps, and no hidden workflow state.
8. When the user asks for a loop or next steps, answer with a short ordered sequence of actions and commands rather than a broad explanatory essay.
9. When helpful, use `@./references/authoring-loop.md` for the loop and `@./references/artifact-inspection.md` for the evidence order.
