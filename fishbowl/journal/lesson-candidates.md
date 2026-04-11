# Fishbowl Lesson Candidates

Use this file for findings that are real enough to keep but not stable enough to promote into `lessons/` yet.

Current status:

- `candidate`: In a thin external repo, the builder needs a fixture-first and file-count-capped first pass or the local-model worker may stall trying to infer too much bootstrap work.
  `evidence_paths`: `fishbowl/.opencode/agents/shipwright.md`, `fishbowl/.opencode/skills/fishbowl-builder/SKILL.md`
  `next`: Rerun the first builder pass with an explicit fixture-only target such as `fixtures/farm-state.json` and `fixtures/farm-events.jsonl`.
- `candidate`: Headless `opencode run` with explicit `@subagent` prompts is still less reliable than primary-agent planning on the local model, so smoke tests should treat the primary `overseer` path as the baseline.
  `evidence_paths`: `fishbowl/journal/sessions/2026-04-10-opencode-smoke-rounds.md`, `fishbowl/.opencode/agents/overseer.md`
  `next`: Prefer overseer-led smoke runs and gather more evidence from interactive TUI usage before redesigning the subagent layout.

Promoted:

- `promoted`: Config-location and child-schema handoff contracts graduated into `lessons/2026-04-10-local-opencode-child-handoff-contracts.md` after the fix-and-rerun smoke cycle.
  `evidence_paths`: `fishbowl/journal/sessions/2026-04-10-opencode-smoke-rounds.md`, `fishbowl/journal/sessions/2026-04-10-opencode-smoke-rounds-followup.md`, `lessons/2026-04-10-local-opencode-child-handoff-contracts.md`
  `next`: Apply the same handoff rule to future local-model fishbowl agents instead of rediscovering it.
