# Molt Fishbowl

This folder is a self-contained opencode experiment surface for local-model baby molts.

The intended end state is not just a browser game. The 1602-style world becomes a visual shell over a running Molt Farm, where islands stand in for agents, crops stand in for skills, and boats stand in for agent-to-agent task flow.

It owns:

- `opencode.json`
- project-local opencode agents and skills
- fishbowl rules
- durable journal and backlog files

It does not own:

- the 1602-style browser-game source repo
- Molt runtime code under `packages/`
- canonical root skills or eval suites

## First Run

1. Copy `config/target.example.json` to `config/target.local.json`.
2. Point `repo_path` at the external game repo.
3. Start the local `llama.cpp` server on `http://127.0.0.1:8080/v1`.
4. Run `opencode` from this directory.

The default agent is `overseer`. It can delegate only to `shipwright`, `scout`, and `scribe`.

Use the journal files under `journal/` as the long-running memory for this experiment.
Start with `journal/plans/2026-04-10-molt-farm-visualization-plan.md` for the world-model and phased build plan.
