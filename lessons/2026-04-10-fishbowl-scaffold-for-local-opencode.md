# Fishbowl Scaffold For Local Opencode

Source:
- fishbowl rules: `fishbowl/AGENTS.md`
- fishbowl config: `fishbowl/opencode.json`
- fishbowl agents: `fishbowl/.opencode/agents/overseer.md`, `fishbowl/.opencode/agents/shipwright.md`, `fishbowl/.opencode/agents/scout.md`, `fishbowl/.opencode/agents/scribe.md`
- fishbowl skills: `fishbowl/.opencode/skills/fishbowl-overseer/SKILL.md`, `fishbowl/.opencode/skills/fishbowl-builder/SKILL.md`, `fishbowl/.opencode/skills/fishbowl-browser-check/SKILL.md`, `fishbowl/.opencode/skills/fishbowl-journal/SKILL.md`
- fishbowl journal: `fishbowl/journal/backlog.md`, `fishbowl/journal/decisions.md`, `fishbowl/journal/templates/session-template.md`
- repo docs: `README.md`, `AGENTS.md`
- validation method: checked-in scaffold review, narrow filesystem test, and draft system-map rerun

## Self-Contained Fishbowl Folder Lesson

- `lesson`: A long-running opencode experiment is easier to evolve and eventually extract when its config, agents, skills, and journal live under one top-level subtree.
- `evidence`: The new fishbowl scaffold keeps `opencode.json`, `.opencode/agents/`, `.opencode/skills/`, `AGENTS.md`, and the journal files together under `fishbowl/` instead of spreading them across the main runtime paths.
- `scope`: experiment scaffolding for future external projects
- `reuse`: When a repo-hosted experiment may later become a separate project or submodule, start with one self-contained top-level folder and explicit boundaries.

## Short-Step Local-Agent Lesson

- `lesson`: Local-model agent prompts work better when each agent owns one skill and answers in short ordered operational steps.
- `evidence`: The fishbowl scaffold gives `overseer`, `shipwright`, `scout`, and `scribe` one matching skill each, and every fishbowl skill requires compact ordered output fields instead of broad narrative responses.
- `scope`: local-model agent design
- `reuse`: When testing small local agents, keep prompts short, keep responsibilities narrow, and make stop conditions explicit so the run stays observable.

## External Target Boundary Lesson

- `lesson`: Keep the target application repo outside the skill-foundry repo and bind it through local config when the goal is to study agent behavior rather than absorb the product code.
- `evidence`: `fishbowl/config/target.example.json` points at an external repo path, `fishbowl/.gitignore` excludes `config/target.local.json`, and both fishbowl and root docs state that the 1602-style game source does not belong in this repo.
- `scope`: local experiment boundaries
- `reuse`: When a local agent experiment needs to point at another codebase, keep the target external, gate access through local config, and preserve the host repo for prompts, evidence, and lessons.
