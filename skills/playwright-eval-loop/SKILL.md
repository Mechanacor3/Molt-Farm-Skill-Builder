---
name: playwright-eval-loop
description: Validate browser-based behavior with a tight evidence loop. Use when a web game or web toy needs Playwright checks, observed failures, and a concise next-pass recommendation.
---

# Playwright Eval Loop

Use this skill when:
- A browser game needs real browser validation.
- You need evidence before changing mechanics, balance, or polish.
- A failing browser behavior should be reduced to a short, testable next pass.

Instructions:
1. Start from observed behavior, not assumptions.
2. Capture the smallest useful evidence set:
   - what was attempted
   - what happened in the browser
   - notable console output
   - whether the result is reproducible
3. Reduce the next pass to one main fix or check. Do not propose a broad rewrite when one failing interaction is enough to guide the next iteration.
4. Prefer artifacts that can be re-read later: test names, screenshots, logs, console warnings, or exact repro steps.
5. When reporting, use exactly these fields:
   observed:
   likely_cause:
   next_check:
   evidence:
6. When useful, read `@./references/evidence-template.md`.
