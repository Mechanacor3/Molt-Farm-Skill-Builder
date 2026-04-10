---
name: fishbowl-browser-check
description: Capture browser evidence, likely cause, and one reproducible next check for the fishbowl target repo.
compatibility: opencode
---

# Fishbowl Browser Check

Use this skill when:
- A browser-game claim needs evidence.
- The next pass should be guided by observed behavior.
- You need one reproducible next check, not a rewrite.

Instructions:
1. Read `config/target.local.json` from the fishbowl working directory first.
2. If the target config is missing or incomplete, stop and return the blocker.
3. Start from observed behavior, not assumptions.
4. Capture only the smallest useful evidence set.
5. Inspect the repo root and at most 2 relevant files before naming a likely cause.
6. If there is no runnable app, no browser log, or no screenshot yet, say so directly and point to the exact existing files.
7. Use exact paths for screenshots, test files, logs, or repro notes.
8. Do not edit files.
9. Return only the five required lines.
10. Report in exactly this order:
   observed:
   likely_cause:
   next_check:
   evidence_paths:
   stop_after:
