---
name: run-summarizer
description: Summarize the outcome of a completed agent run into a concise structured report.
---

# Run Summarizer

Use this skill when:
- A run has completed and needs a short summary.
- You need to capture what was attempted, what happened, and whether it succeeded.
- The output should be suitable for logs and human review.

Instructions:
1. Read only the run record and the smallest immediately relevant output fields.
2. Distinguish the recorded run status from the practical outcome. Do not rewrite `completed` as success unless the output clearly supports that.
3. Produce exactly these fields in this order:
   attempted: one sentence
   happened: one or two short evidence-backed sentences
   status: completed, failed, or partial
   produced: outputs, artifacts, or notable side effects
   gaps: the most important missing validation, uncertainty, or unverified assumption; use `none` if there is no meaningful gap
   next_step: the single best follow-up action; use `none` if no action is needed
4. Prefer concrete nouns over narration. Name run ids, workflow names, files, logs, or artifacts when they matter.
5. Keep the whole summary compact. No greetings, no meta commentary, no extra headings.
6. Do not speculate about unseen context. If the run did not verify something, say so plainly in `gaps`.
7. When useful, follow the output template in `@./references/run-summary-template.md`.
