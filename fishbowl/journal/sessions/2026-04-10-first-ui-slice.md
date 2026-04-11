# First Fishbowl UI Slice

goal:
Build the first 1602-ish browser screen that makes the fishbowl metaphor readable as a visual shell over agents, skills, and handoffs.

attempted:
Turned the external target repo into a static browser app with a harbor-styled world layer, four islands, skill fields, boat routes, an inspector panel, and a replay-style event timeline. Added `fixtures/farm-state.json` and `fixtures/farm-events.jsonl`, wired the UI to load them over HTTP, and added a narrow fixture validation script behind `npm test`.

evidence_paths:
- /tmp/fishbowl-1602-target/index.html
- /tmp/fishbowl-1602-target/src/styles.css
- /tmp/fishbowl-1602-target/src/main.js
- /tmp/fishbowl-1602-target/fixtures/farm-state.json
- /tmp/fishbowl-1602-target/fixtures/farm-events.jsonl
- /tmp/fishbowl-1602-target/scripts/validate-fixtures.mjs

decision:
Keep the first UI slice framework-free and fixture-driven. The visualizer is now strong enough to serve as the design reference for the live fishbowl, and the next meaningful step is to replace hand-authored replay language with one real exported Molt run.

next:
Feed one real run into the same `farm-state.json` and `farm-events.jsonl` contract, then tune the inspector and timeline around that evidence instead of around stub events.
