---
name: game-balance-pass
description: Improve pacing, fairness, scoring, and challenge after a browser game is already playable. Use when the main issue is game feel through balance rather than broken mechanics or visual polish.
---

# Game Balance Pass

Use this skill when:
- The game is already playable.
- The main problem is pacing, fairness, reward timing, or difficulty spikes.
- You need a focused tuning pass instead of a rebuild.

Instructions:
1. Tune only after the loop is stable enough to replay.
2. Pick one main balance target:
   - difficulty ramp
   - scoring rate
   - enemy or obstacle pacing
   - resource frequency
   - reward timing
3. Explain the change in player-facing terms, not only implementation terms.
4. Keep the pass measurable. State what should feel different after the change and how to verify it.
5. Report with these fields:
   balance_target:
   change:
   expected_player_effect:
   recheck:
6. When useful, read `@./references/balance-heuristics.md`.
