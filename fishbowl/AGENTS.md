# Fishbowl Rules

This subtree is a local-first opencode fishbowl for small agents working against an external browser-game repo.

## Boundaries

- The game repo stays outside this repo.
- Read `config/target.local.json` before any external-repo action.
- If `config/target.local.json` is missing or incomplete, stay in planning and journaling mode.
- Do not copy game source into `fishbowl/`.

## Working Style

- Prefer short ordered actions over essays.
- Use exact file paths when naming evidence or changed files.
- Take one narrow pass at a time.
- Stop after one concrete pass instead of silently chaining more work.
- Keep local-model prompts compact and operational.

## Agent Roles

- `overseer` chooses one next action and delegates one bounded pass.
- `shipwright` builds or repairs the smallest playable browser-game slice.
- `scout` gathers browser evidence and reproducible checks without editing files.
- `scribe` updates the fishbowl journal, decisions, and lesson candidates.

## Journal

- Use `journal/templates/session-template.md` for new session notes.
- Keep `journal/backlog.md` current at the level of one next playable slice.
- Put tentative findings in `journal/lesson-candidates.md` before promoting them into repo-wide lessons.
- After a fishbowl pass has repeated evidence or survives one fix-and-rerun cycle, extract the smallest stable repo lesson into `lessons/` instead of leaving everything in candidates.
- If a pass does not produce a repo lesson, say why in the session note so the gap stays visible.

## Safety

- Keep sharing disabled.
- Keep web access disabled unless the repo itself proves it is needed later.
- Treat external-directory access as approval-gated by default.
- Do not work around one-skill-per-agent restrictions.
