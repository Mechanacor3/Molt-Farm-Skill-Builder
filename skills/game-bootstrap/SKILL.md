---
name: game-bootstrap
description: Create or repair the first playable slice of a browser game. Use only when the immediate task is scaffolding a minimal core loop, rebuilding a broken base loop, or adding deterministic hooks before broader iteration. Prefer a higher-level coordination skill for generic “build me a browser game” requests.
---

# Game Bootstrap

Use this skill when:
- A browser game is starting from scratch.
- The existing prototype is too broken to support meaningful balance or polish work.
- You need a stable first loop with predictable hooks for later evaluation.
- The current question is specifically about bootstrap or core-loop repair, not the whole game-development loop.

Instructions:
1. Build the smallest playable slice first: one mechanic, one control scheme, one fail or win condition.
2. Prefer a plain, inspectable structure over framework cleverness. The goal is to make the game easy to test and easy to revise.
3. Add deterministic hooks early when possible:
   - a stable restart path
   - inspectable game state
   - deterministic time or spawn controls for tests
4. Keep the first artifact narrow:
   outline:
   files_to_touch:
   playable_loop:
   debug_hooks:
   first_check:
5. Do not mix in later-stage balance or polish goals unless the user explicitly asks.
6. If the request is broader than bootstrap, let a higher-level coordination skill own the plan and use this skill only for the narrow build step.
7. When useful, read `@./references/bootstrap-checklist.md`.
