# Local Opencode Child Handoff Contracts

Source:
- fishbowl smoke session: `fishbowl/journal/sessions/2026-04-10-opencode-smoke-rounds.md`
- fishbowl smoke follow-up: `fishbowl/journal/sessions/2026-04-10-opencode-smoke-rounds-followup.md`
- fishbowl candidates: `fishbowl/journal/lesson-candidates.md`
- overseer agent: `fishbowl/.opencode/agents/overseer.md`
- shipwright agent: `fishbowl/.opencode/agents/shipwright.md`
- scout agent: `fishbowl/.opencode/agents/scout.md`
- overseer skill: `fishbowl/.opencode/skills/fishbowl-overseer/SKILL.md`
- builder skill: `fishbowl/.opencode/skills/fishbowl-builder/SKILL.md`
- browser-check skill: `fishbowl/.opencode/skills/fishbowl-browser-check/SKILL.md`

## Config Location Lesson

- `lesson`: In local-model opencode delegation, every child prompt should restate where shared config lives instead of assuming the subagent will resolve it correctly.
- `evidence`: Early `@shipwright` and `@scout` smokes drifted because child passes inferred `config/target.local.json` might live inside the external repo, while the follow-up smokes improved after the prompts explicitly said the config is read from the fishbowl working directory and not from inside `repo_path`.
- `scope`: local-model subagent handoff design
- `reuse`: When a parent agent delegates local-model work that depends on shared config, restate the config path in the delegated prompt even if the child skill already mentions it.

## Child Schema Lesson

- `lesson`: In local-model opencode delegation, the parent prompt should copy the child agent's exact output schema into the Task prompt rather than relying on role names like “builder format” or “scout format.”
- `evidence`: The first fishbowl smokes produced wrong-format child behavior until `overseer` was tightened to emit `Task(description=..., prompt=..., subagent_type=...)` with the child schema spelled out, after which the exported child sessions followed the right config path and narrower task framing.
- `scope`: local-model delegated prompt contracts
- `reuse`: When a parent agent needs bounded child output from a small local model, include the exact field list in the delegated prompt and treat that contract as part of the handoff payload.

## Overseer Baseline Lesson

- `lesson`: For headless local-model smoke runs, treat the primary overseer path as the baseline signal and use child-session exports as secondary evidence.
- `evidence`: Across the fishbowl opencode smokes, `overseer` consistently produced the bounded next action and the correct `Task(...)` handoff while deeper child passes still hit wall-clock limits, making exported child traces more reliable than top-level completion status for diagnosing progress.
- `scope`: headless local-model smoke methodology
- `reuse`: When validating a delegated local-model workflow in headless mode, trust the primary planner first, then inspect child exports to judge whether the bottleneck is contract quality or runtime depth.
