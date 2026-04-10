# Fishbowl Backlog

## Now

- Bind the first external 1602-style browser-game repo through `config/target.local.json`.
- Keep the fishbowl local-only, approval-gated, and one-skill-per-agent.
- Turn the 1602 metaphor into a concrete visual contract for agents, skills, and agent-agent communication.
- Define the minimum replayable event/state JSON that the external browser game will consume.

## Next

- Build one non-live browser slice that shows a few islands, skill fields, and one boat route from fixture data.
- Replay one real Molt run through the visual layer using exported state and event fixtures.
- Add browser evidence capture and replay checks for the visualization slice.
- Record each fishbowl pass in `journal/sessions/`.

## Later

- Switch from replay-only to live feed from a running Molt Farm.
- Make island, crop, and boat inspectors open real run, log, and artifact references.
- Promote stable fishbowl prompts into root `skills/` with hand-authored evals.
- Add balance and polish agents only after the playable loop is stable.
- Decide whether `fishbowl/` should become a separate submodule.

## Done

- Scaffold the fishbowl opencode surface, journal, and lesson seed files.
- Write the first concrete fishbowl visualization plan.
