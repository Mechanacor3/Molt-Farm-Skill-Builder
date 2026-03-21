---
name: develop-web-game
description: Build or improve a small browser game through a tight iterative loop. Use when the task is to create, test, observe, refine, and measure a web game or web toy without loading broad context all at once.
---

# Develop Web Game

Use this skill when:
- You are building a browser game or playful web toy from scratch.
- You are iterating on an existing game and want a short human-feedback loop.
- The task needs a disciplined loop instead of a one-shot implementation.

Instructions:
1. Treat this as a coordination skill. Keep the overall loop visible, then activate narrower skills only when they are needed.
2. Start with the smallest playable version of the game. Prefer one clear mechanic, one control scheme, and one win or fail condition before adding depth.
3. Follow this loop:
   scope -> build -> validate -> observe -> improve -> measure
4. Activate component skills selectively:
   - Use `game-bootstrap` when starting a new game or rebuilding a broken base loop.
   - Use `playwright-eval-loop` when the game must be checked in the browser or a behavior claim needs evidence.
   - Use `game-balance-pass` only after the game is playable and stable.
   - Use `game-polish-pass` last, after the main mechanic and browser checks are reliable.
5. Keep each pass focused. Change one main dimension at a time: playability, stability, balance, or polish.
6. Prefer evidence over intuition. If a browser check, test, screenshot, console error, or user report exists, use that to choose the next pass.
7. Do not let polish expand scope early. Fancy visuals, content breadth, and animation can wait until the loop works.
8. When the task is planning or review oriented, produce exactly these fields in this order:
   goal:
   current_evidence:
   next_phase:
   use_skills:
   build_step:
   validation_step:
   stop_after:
9. When the task is implementation oriented, still keep those seven ideas visible in your internal plan and final summary.
10. When useful, read `@./references/dev-loop.md` and `@./references/component-map.md`.
