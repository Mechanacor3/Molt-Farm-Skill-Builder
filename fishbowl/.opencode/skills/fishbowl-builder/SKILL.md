---
name: fishbowl-builder
description: Build or repair the smallest playable browser-game slice in the external fishbowl target repo.
compatibility: opencode
---

# Fishbowl Builder

Use this skill when:
- The next fishbowl pass is about building or repairing a browser-game slice.
- The target repo is external and defined in `config/target.local.json`.
- The goal is one playable step, not a broad rewrite.

Instructions:
1. Read `config/target.local.json` first.
2. If the target config is missing or `repo_path` is empty, stop and return only the blocker.
3. Build the smallest playable slice first:
   - one control scheme
   - one ship action
   - one island interaction
   - one restart path
4. Prefer inspectable structure and deterministic hooks over polish.
5. Change one main dimension only: bootstrap or core-loop repair.
6. Use short ordered actions, not essays.
7. Report in exactly this order:
   goal:
   current_slice:
   next_change:
   files_or_paths:
   check:
   stop_after:
