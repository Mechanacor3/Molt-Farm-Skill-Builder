# Conversational Eval Authoring Lessons

Source:
- feature: `packages/moltfarm/eval_authoring.py`
- CLI surface: `packages/moltfarm/cli.py`
- internal authoring skill: `skills/eval-author/SKILL.md`
- validation method: unit test suite plus local Codex skill installation review

## Draft-First Lesson

- `lesson`: Conversational eval creation should write a reviewable draft workspace before it touches canonical `evals/` files.
- `evidence`: The implemented `create-evals` flow writes `session.json`, probe outputs, suggested flavors, draft fixtures, and `draft/evals.json` under `skills/<skill>/evals/workspace/create-evals/session-N/`, and only promotes into canonical files on explicit `--promote`.
- `scope`: eval authoring workflow
- `reuse`: When adding authoring or refinement flows to this repo, keep the first pass additive and inspectable so the user can review artifacts before promotion.

## Additive Merge Lesson

- `lesson`: Generated eval authoring should preserve existing canonical cases verbatim and append normalized new cases instead of rewriting the suite wholesale.
- `evidence`: The draft builder keeps prior `evals/evals.json` cases, de-duplicates generated case ids with suffixes such as `-2`, and avoids overwriting existing fixture files by renaming generated draft fixtures when needed.
- `scope`: eval suite mutation
- `reuse`: Prefer append-and-normalize behavior for generated eval content unless the user explicitly asks for destructive rewrite semantics.

## Skill-Backed Runtime Lesson

- `lesson`: Repo-specific workflow behavior is easier to evolve when the runtime is backed by a local skill artifact rather than hidden prompt text.
- `evidence`: The new `eval-author` behavior lives in `skills/eval-author/SKILL.md`, while the runtime module focuses on session lifecycle, probe orchestration, and artifact writing.
- `scope`: skill-builder runtime design
- `reuse`: When a new capability contains reusable review logic or domain guidance, capture that guidance as a portable skill and keep the runtime layer narrow.

## Repo-Fit Installation Lesson

- `lesson`: When exposing repo-local skills to Codex, install the repo-shaped set rather than every local skill indiscriminately.
- `evidence`: The local Codex skill install kept `molt-cli`, `eval-author`, `lesson-extractor`, `repo-triage`, `run-summarizer`, `skill-finder`, `skill-refiner`, `python-build`, and `docker-smoke-test`, while leaving game-specific skills out of the default set.
- `scope`: local skill installation
- `reuse`: Treat Codex local skill installation as part of repo ergonomics; pick the subset that matches the repo’s actual workflow and avoid unrelated clusters by default.
