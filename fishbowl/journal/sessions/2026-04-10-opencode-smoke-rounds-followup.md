# Fishbowl Opencode Smoke Rounds Follow-up

goal:
Rerun bounded `@shipwright` and `@scout` headless smokes after tightening config-location and child-schema instructions, then record what actually improved.

attempted:
Patched the fishbowl agent and skill prompts so delegated passes explicitly say that `config/target.local.json` is read from the fishbowl working directory, not inside `repo_path`, and so `overseer` writes the delegated `Task(...)` call using the child agent's exact output schema. Then reran one `overseer`, one `@shipwright`, and one `@scout` smoke against the same local target repo.

evidence_paths:
- fishbowl/.opencode/agents/overseer.md
- fishbowl/.opencode/agents/shipwright.md
- fishbowl/.opencode/agents/scout.md
- fishbowl/.opencode/skills/fishbowl-overseer/SKILL.md
- fishbowl/.opencode/skills/fishbowl-builder/SKILL.md
- fishbowl/.opencode/skills/fishbowl-browser-check/SKILL.md
- fishbowl/journal/lesson-candidates.md

decision:
Keep the config-location and child-schema changes. The new smokes show real improvement: `overseer` now emits the exact `Task(description=..., prompt=..., subagent_type=...)` form, and both child sessions read `config/target.local.json` from the fishbowl working directory instead of incorrectly probing inside the external repo. Do not keep tightening prompts just to chase wall-clock completion; the next bottleneck looks like local-model latency during deeper child passes, not a broken contract.

next:
Keep headless smoke focused on `overseer` as the baseline, and treat child-session exports as the main evidence source for now. Revisit deeper speed/termination tuning only after a few interactive `opencode` TUI runs show the same stall pattern.
