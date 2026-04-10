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

## Follow-up Smoke Notes

goal:
Run a few headless fishbowl rounds through opencode and tighten the agent surface where the local model stumbles.

attempted:
Ran one overseer planning round successfully, then tried a `@shipwright` headless delegation round and observed a Task-tool failure because the delegated call omitted a required `description` field.

evidence_paths:
- fishbowl/opencode.json
- fishbowl/.opencode/agents/overseer.md
- fishbowl/.opencode/skills/fishbowl-overseer/SKILL.md
- fishbowl/journal/lesson-candidates.md

decision:
Keep the agent layout, but make the Task-tool call shape explicit in the overseer prompt and skill before further smoke runs.

next:
Rerun `@shipwright` and `@scout` after the delegation-shape fix, then keep only the changes that measurably improve headless local-model behavior.
