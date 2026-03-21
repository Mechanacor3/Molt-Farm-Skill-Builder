---
name: game-bootstrap
description: Create the smallest stable playable slice of a browser game. Use when a web game needs an initial scaffold, a repaired core loop, or deterministic hooks before broader iteration.
---

# Game Bootstrap

Use this skill when:
- A browser game is starting from scratch.
- The existing prototype is too broken to support meaningful balance or polish work.
- You need a stable first loop with predictable hooks for later evaluation.

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
6. When useful, read `@./references/bootstrap-checklist.md`.
