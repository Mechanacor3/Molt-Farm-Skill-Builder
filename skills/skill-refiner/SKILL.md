---
name: skill-refiner
description: Improve an existing skill by applying lessons, tightening scope, and clarifying instructions.
---

# Skill Refiner

Use this skill when:
- A skill needs clearer instructions or narrower scope.
- Lessons from runs should be folded back into `SKILL.md`.
- You need to revise a skill without changing the overall architecture.

Instructions:
1. Read the target skill first, then any directly relevant lesson, grading, feedback, benchmark, or trace context.
2. Treat failed assertions, reviewer complaints, and execution traces as the strongest signals for revision.
3. Preserve the skill's intent and keep the revision minimal.
4. Generalize from the evidence. Fix underlying patterns rather than patching only one prompt.
5. Prefer clearer triggers, tighter steps, fewer ambiguous instructions, and short reasoning-based guidance.
6. If repeated work should become a bundled script, reference, or example, say so explicitly.
7. Keep the result portable, human-readable, and local-first.
8. Do not add runtime concerns, UI concepts, or broad new behaviors.
9. Produce exactly these sections in this order:
   Summary: two or three sentences on what should change and why.
   Proposed SKILL.md: the full revised skill content.
   Expected Eval Impact: two or three bullets naming what should improve.
   Follow-up Checks: one to three concrete checks or eval cases to rerun.
10. Use `@./references/refinement-checklist.md` to keep revisions narrow and reviewable.
