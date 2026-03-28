---
name: eval-author
description: Analyze an existing skill, inspect nearby evidence, and draft additive eval flavors, cases, and fixtures.
---

# Eval Author

Use this skill when:
- A local `SKILL.md` exists but its `evals/evals.json` coverage is weak, missing, or obviously narrow.
- You need to turn skill instructions, prior eval artifacts, and a few probe runs into stronger eval drafts.
- The goal is to extend inspectable local eval files, not to build a chat surface or hidden workflow state.

Instructions:
1. Start with the target skill's real instructions, existing evals, relevant lessons, and latest eval workspace artifacts.
2. Treat `with_skill` versus `without_skill` probe evidence as a hint about likely coverage gaps, not as a final benchmark.
3. Suggest a small set of distinct eval flavors that materially improve task coverage.
4. Prefer realistic prompts, goal/evidence checks, and narrow local fixtures over generic style checks.
5. Keep draft cases additive. Preserve existing canonical eval cases rather than rewriting them.
6. Generate fixture files only when they materially improve inspectability or coverage.
7. Keep fixtures plain and local-first: Markdown, text, or JSON.
8. Avoid broad repo dumps, hidden state, or instructions that require extra orchestration.
9. When a case uses files, make the file references concrete and skill-local.
10. Prefer evals that help the loop `test -> observe -> lesson -> improve -> measure`.
