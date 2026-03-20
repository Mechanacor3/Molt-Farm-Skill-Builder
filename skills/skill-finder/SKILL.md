---
name: skill-finder
description: Choose the best existing skill or small set of skills for a task, explain why, and identify the smallest missing skill when the current set is not enough. Use before creating a new skill or wiring a workflow.
---

# Skill Finder

Use this skill when:
- You need to decide which existing skills fit a task.
- You want to know whether a new skill is actually needed.
- You want a concise recommendation before building or refining a workflow.

Instructions:
1. Read the task and the provided skill inventory only.
2. Prefer reusing an existing skill over proposing a new one.
3. Recommend at most three skills.
4. For each recommended skill, explain the fit in one sentence.
5. If the current set is insufficient, propose exactly one missing skill with:
   missing_skill: short slug-like name
   reason: one sentence
   scope: one sentence describing the narrow job it should do
6. Keep the output concise and operational.
7. Use this rubric when helpful: @./references/selection-rubric.md
