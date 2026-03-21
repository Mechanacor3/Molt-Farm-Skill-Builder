---
name: develop-web-game
description: Coordinate the full loop for building or improving a small browser game. Use when the user asks for a browser-playable game, game prototype, game jam toy, or iterative game improvement and the task should move through scope, build, validate, observe, improve, and measure rather than jumping straight to one narrow pass.
---

# Develop Web Game

Use this skill when:
- You are building a browser game or playful web toy from scratch.
- You are iterating on an existing game and want a short human-feedback loop.
- The task needs a disciplined loop instead of a one-shot implementation.
- The user asks for a platformer, arcade game, puzzle game, game jam prototype, or other small browser-playable game, even if they do not name this skill explicitly.
- The request is broad enough that bootstrap, browser validation, balance, and polish may all matter over time, even if only one phase comes first right now.

Instructions:
1. Treat this as the top-level coordination skill for generic browser-game requests. Keep the overall loop visible, then activate narrower skills only when they are needed.
2. Start with the smallest playable version of the game. Prefer one clear mechanic, one control scheme, and one win or fail condition before adding depth.
3. Follow this loop:
   scope -> build -> validate -> observe -> improve -> measure
4. Activate component skills selectively:
   - Use `game-bootstrap` only when the immediate need is scaffolding the first playable slice or repairing a broken core loop.
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
11. If another game-related skill also seems relevant, keep this skill as coordinator unless the user is explicitly asking only for that narrower pass.
