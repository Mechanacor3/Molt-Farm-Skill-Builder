---
name: lesson-extractor
description: Extract actionable lessons from run logs and completed runs.
---

# Lesson Extractor

Use this skill when:
- A run or log has completed and should be reviewed for improvement.
- You want to identify mistakes, inefficiencies, surprises, or better patterns.
- The output should become a reusable lesson, not a chat response.

Instructions:
1. Read only the provided run, log, benchmark, grading, or comparison context.
2. Identify the smallest set of actionable lessons.
3. Keep each lesson specific, attributable, and short.
4. Prefer concrete behavior changes over general advice.
5. If a comparison or benchmark is provided, cite its winner, category delta, or cost delta instead of relying only on the raw output text.
6. Do not expand beyond the evidence in the input.
7. Use `@./references/lesson-format.md` to keep lessons short and reusable.
