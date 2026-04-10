---
name: llm-wiki-validator
description: Review a proposed LLM wiki update plan or wiki page change for source-path evidence, canonical page routing, duplicate avoidance, taxonomy fit, and link discipline. Use when the task is to critique or validate a wiki update before editing.
---

# LLM Wiki Validator

Use this skill when:
- A proposed wiki update plan should be reviewed before anyone edits files.
- A draft wiki page change may be inventing facts, creating duplicates, or breaking the existing taxonomy.
- The task is review and validation, not authoring the wiki content itself.

Instructions:
1. Inspect the target wiki conventions first: taxonomy, canonical pages, index pages, and link style.
2. Review the proposed plan or draft change against the provided source material only.
3. Flag any non-obvious fact that is missing an exact supporting source path.
4. Flag duplicate-page risk, spelling-variant splits, or any proposal that bypasses an existing canonical page.
5. Flag taxonomy drift when the plan invents new top-level folders or page types even though a working structure already exists.
6. Prefer narrow corrections over broad redesigns. If the plan is salvageable, say exactly how to repair it.
7. When the plan is sound, approve it briefly and name any residual uncertainty.
8. Produce exactly these sections in this order:
   Verdict: `approve` or `revise`
   Findings: short bullets naming the concrete problem or `none`
   Repairs: short bullets naming the smallest corrections or `none`
   Evidence: short bullets naming the supporting source paths or `none`
9. If the task is to actually author or extend wiki pages rather than review a plan, use `llm-wiki` instead.
10. When helpful, use `@./references/review-checklist.md`.
