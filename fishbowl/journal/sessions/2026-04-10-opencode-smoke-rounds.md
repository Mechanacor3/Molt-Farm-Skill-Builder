# Fishbowl Opencode Smoke Rounds

goal:
Run a few local-model opencode rounds against the fishbowl and tighten the repo-side configuration or prompts where behavior is clearly weak.

attempted:
Ran a successful read-only overseer round, fixed an invalid top-level permission shape in `fishbowl/opencode.json`, tightened overseer Task-tool delegation requirements, then reran builder and scout-style prompts against a tiny external target repo.

evidence_paths:
- fishbowl/opencode.json
- fishbowl/.opencode/agents/overseer.md
- fishbowl/.opencode/agents/shipwright.md
- fishbowl/.opencode/skills/fishbowl-overseer/SKILL.md
- fishbowl/.opencode/skills/fishbowl-builder/SKILL.md
- fishbowl/journal/lesson-candidates.md

decision:
Keep the config and prompt fixes that improved startup and delegation shape. Do not broaden the fishbowl yet; local-model headless subagent execution still looks less reliable than primary-agent planning.

next:
Use the fishbowl primarily through `overseer` for headless smoke, treat builder passes as fixture-first and tightly bounded, and revisit direct subagent smoke only after more evidence from TUI or live interactive runs.
