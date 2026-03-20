---
name: log-writer
description: Create a clean append-only log entry for a completed agent run.
---

# Log Writer

Use this skill when:
- A run has completed and needs a durable log entry.
- You need to record the inputs, actions, and observed result in a simple file-based format.
- The output should be concise and suitable for later review or lesson extraction.

Instructions:
1. Read the run record and any immediately relevant output summary.
2. Capture the inputs, scope, key actions, notable events, and result.
3. Keep the entry append-only, factual, and brief.
4. Do not add analysis beyond the observed run behavior.
5. Use the structure in `@./references/log-entry-template.md` when it helps keep entries consistent.
