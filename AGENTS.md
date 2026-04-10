# AGENTS.md

## Project: Molt Farm Skill Builder

Molt Farm Skill Builder is a local-first workspace for building, evaluating, and recursively improving `SKILL.md` capabilities.

This repo is not a chat app, not a general agent playground, and no longer primarily an agent control plane.

The center of gravity is:

- `skills/`
- `lessons/`
- eval artifacts
- evidence from runs and logs

Favor simple, inspectable, file-based designs over clever abstractions.

---

## Product Intent

The core loop of this repository is:

**Test → Observe → Lesson → Improve → Measure**

Use code to support that loop. Do not let the runtime become the product.

The system should make it easy to:

- evaluate local skills against realistic prompts
- compare a skill to a baseline or prior snapshot
- inspect exactly what happened
- extract actionable lessons
- fold those lessons back into better skills

---

## Project Memory

Treat this file as the durable memory for repository-level preferences and instructions.

If the user says to "remember" something for this repo, record it here or in another file discoverable through this same `AGENTS.md` mechanism.

Current durable preferences:
- prefer local-first, minimal-exposure defaults
- prefer tracing disabled unless there is a clear reason to enable it
- prefer narrow context, inspectable files on disk, and low-export behavior by default
- treat the repo as a skill foundry: look for reusable capabilities that should become portable `SKILL.md` artifacts
- remember to keep work moving into git in small, coherent commits instead of leaving useful repo changes uncommitted
- record meaningful implementation lessons in `lessons/` as part of feature work, not only after an explicit reminder

---

## Scope

Primary artifacts:
- `skills/` = reusable capabilities anchored by `SKILL.md`
- `lessons/` = distilled improvements
- `wiki/` = curated workflow-first system map distilled from lessons
- `logs/` = append-only observations
- `runs/` = durable execution records
- `packages/` = minimal runtime code that supports the skill loop

Non-product or optional areas:
- `experiments/` = optional research tooling that should not shape the main product surface
- `tmp/` = local scratch artifacts
- `example_upstream_skills/` = ignored local study material, not part of the runtime

---

## CLI Guidance

The default command shape is:

`molt skill-builder ...`

Prefer:
- `./molt skill-builder run <operation> --input key=value`
- `./molt skill-builder eval-skill <skill>`

Use the CLI lightly and inspectably:
- prefer narrow inputs over broad repo dumps
- treat the CLI as an execution surface, not a chat surface
- inspect artifacts after commands finish instead of guessing

After running commands, look at:
- `runs/`
- `logs/YYYY-MM-DD/`
- `lessons/`
- `skills/<skill>/evals/workspace/iteration-N/`

---

## Design Principles

### 1. Local-first

Assume local development, local files, and local inspection first.

### 2. Least context by default

Prefer:
- narrow prompts
- explicit file inputs
- eval artifacts over broad summaries
- references loaded on demand

Do not casually pass full repo context, unrelated logs, or broad histories into runs.

### 3. Keep file formats inspectable

Prefer plain files:
- Markdown
- YAML
- JSON

Avoid hidden state whenever a file artifact will do.

### 4. Prefer boring code

Prefer:
- small modules
- explicit data structures
- simple control flow
- minimal magic

Avoid:
- speculative frameworks
- plugin systems before they are needed
- distributed-system thinking for local workflows

### 5. Skills are first-class

Whenever repeated logic, instructions, or review patterns appear, ask:
- could this become a skill?
- should this refine an existing skill?
- does this belong in `references/`, `scripts/`, or `examples/`?

The long-term value is in the skill library, not the scaffolding.

---

## Current Priorities

### Priority 1: Skill quality loop

Support a minimal, real loop for:
- authored eval cases
- with-skill vs baseline runs
- grading
- lessons
- refinement
- rerun

### Priority 2: Skill loading

Keep `SKILL.md` loading simple, robust, and compatible with common upstream layouts.

### Priority 3: Eval artifacts

Every meaningful skill evaluation should produce inspectable artifacts on disk:
- outputs
- grading
- timing
- traces
- benchmarks
- feedback placeholders

### Priority 4: Lessons

Promote repeated findings into durable lesson files that can drive later refinements.

### Priority 5: CLI usability

Keep the `molt skill-builder ...` flow clear and small.

---

## Non-Goals

Do not drift into these unless explicitly needed:

- rich web UI
- general-purpose chat interface
- multi-tenant auth
- distributed orchestration platform
- remote execution dependency for the main loop
- database-first architecture
- marketplace/platform thinking before the local loop is solid

---

## Coding Preferences

### Language

Prefer Python for runtime code unless there is a strong reason otherwise.

### Style

- use clear names
- add concise comments where helpful
- keep functions focused
- keep side effects explicit

### Dependencies

Add dependencies sparingly. Prefer the standard library when it keeps the core loop simple.

---

## Testing Guidance

Favor practical tests around the skill loop.

Useful tests:
- skill discovery works
- eval suites load
- skill evals write expected workspace artifacts
- baselines compare correctly
- lessons can be promoted from real outputs
- CLI routes to the right skill-builder commands

Prefer a few strong tests over many shallow tests.

Unit tests should stub LLM calls where practical.

---

## When Making Changes

When working in this repo:

1. keep the project centered on skill building
2. preserve inspectable artifacts on disk
3. prefer eval-driven refinement over intuition
4. keep the CLI and runtime small
5. avoid turning execution scaffolding into the product
6. leave the skill library better than you found it

If there is ambiguity, choose the path that best supports:

**Test → Observe → Lesson → Improve → Measure**
