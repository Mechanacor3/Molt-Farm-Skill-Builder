# Fishbowl Metaphor Visual Plan

goal:
Turn the 1602 metaphor into a concrete visual plan so the external browser game becomes a readable shell over a running Molt Farm.

attempted:
Mapped islands to agents, crops to skills, boats to handoffs, then wrote a phased plan covering static slice, replay integration, live feed, and a minimum JSON contract.

evidence_paths:
- fishbowl/journal/plans/2026-04-10-molt-farm-visualization-plan.md
- fishbowl/journal/backlog.md
- fishbowl/journal/decisions.md
- fishbowl/README.md

decision:
The first real game slice should be a replayable observability surface with 1602 language, not a full standalone logistics game.

next:
Create fixture-backed `farm-state.json` and `farm-events.jsonl` examples in the external repo and build one static archipelago screen with island, field, boat, inspector, and timeline layers.
