# AGENTS.md

## Project: Molt Farm v2

Molt Farm v2 is a local-first agent control plane for running, logging, and improving agent workflows over time.

This project is **not** a chat app and **not** a generic AI playground.  
It is a system for:

- defining reusable **skills**
- defining executable **agents**
- defining runnable **workflows**
- recording **runs**
- writing **logs**
- distilling **lessons**

Favor simple, inspectable, file-based designs over clever abstractions.

---

## Product Intent

The core loop of this repository is:

**Run → Log → Lesson → Skill → Better Run**

Design decisions should support that loop.

The system should make it easy to:

- run an agent workflow locally
- inspect exactly what happened
- keep context exposure minimal
- promote useful patterns into reusable skills
- evolve safely without platform lock-in

---

## Project Memory

Treat this file as the durable memory for repository-level preferences and instructions.

If the user says to "remember" something for this repo, record it here or in another file that is discoverable through this same `AGENTS.md` mechanism.

Current durable preferences:
- prefer local-first, minimal-exposure defaults
- prefer tracing disabled unless there is a clear reason to enable it
- prefer narrow context, inspectable files on disk, and low-export behavior by default
- treat the repo as a skill foundry: look for reusable capabilities that should become portable `SKILL.md` artifacts

---

## Core Concepts

### Skill
A reusable capability packaged as a folder with a canonical `SKILL.md`.

A skill is:
- portable
- human-readable
- model-readable
- not a runtime container
- not a workflow

Skills live under `skills/<skill-name>/`.

A skill may contain:
- `SKILL.md`
- examples
- helper scripts
- references

Do not invent a replacement for `SKILL.md`.

---

### Agent
An agent is a worker definition that loads one or more skills and executes tasks under a context policy.

An agent is:
- a runtime definition
- not the same thing as a skill
- not the same thing as a Kubernetes pod

Agents live under `agents/<agent-name>/` and are typically defined by `agent.yaml`.

Agent definitions may include:
- model choice
- loaded skills
- tool access
- context policy
- execution hints

Treat the agent definition as durable identity.  
Treat a pod/job/process as one execution instance of that agent.

---

### Workflow
A workflow is a runnable plan that selects an agent, binds inputs, and defines execution behavior.

Workflows live under `workflows/<workflow-name>/` and are typically defined by `molt.yaml`.

A workflow may eventually support:
- manual execution
- CLI execution
- slash-command triggers
- cron/scheduled execution
- multi-step orchestration

For now, keep workflows simple and mostly single-entrypoint.

---

### Run
A run is a single execution record.

Runs should be:
- identifiable
- serializable
- inspectable
- replay-friendly where practical

A run record should capture, at minimum:
- run id
- timestamp
- workflow
- agent
- inputs
- status
- outputs or output summary
- relevant log references

Prefer JSON or YAML files over databases in the early versions.

---

### Log
A log is an append-only record of what happened during or after a run.

Logs should help answer:
- what was attempted
- what context was used
- what happened
- what failed
- what was learned

Keep logs simple and file-based first.

---

### Lesson
A lesson is a distilled insight extracted from one or more logs or runs.

A lesson should be:
- short
- actionable
- attributable
- promotable into a skill or skill revision

Lessons are first-class artifacts, not throwaway notes.

---

## Architectural Direction

Build toward a clean separation:

- `skills/` = reusable capabilities
- `agents/` = worker definitions
- `workflows/` = runnable plans
- `logs/` = append-only records
- `lessons/` = distilled knowledge
- `packages/` = reusable runtime code
- `apps/` = entrypoints and service surfaces

Do not collapse skills, agents, and workflows into one schema.

---

## Design Principles

### 1. Local-first
Assume local development and local inspection first.

The system should work well:
- on a laptop
- in a local repo
- with files on disk
- without requiring cloud infrastructure

Cloud or k8s support may come later, but should not be required for the MVP.

---

### 2. Least context by default
Agents should receive the minimum context required to do their job.

Prefer:
- narrow inputs
- summaries over full dumps
- explicit context contracts
- clear boundaries

Do not casually pass full repo context, full chat history, or unrelated logs into agent execution.

If context policy is not yet fully implemented in code, preserve the concept in interfaces and structure.

Default context mode: `least_context`.

---

### 3. Keep file formats inspectable
Prefer plain files:
- Markdown
- YAML
- JSON

Avoid premature databases, queues, or hidden state.

A developer should be able to inspect the repo and understand:
- available skills
- available agents
- available workflows
- prior runs
- current logs
- accumulated lessons

---

### 4. Prefer boring code
Use straightforward, maintainable code.

Prefer:
- small modules
- explicit data structures
- simple functions
- minimal magic

Avoid:
- over-engineered plugin systems
- heavy framework coupling
- speculative abstractions
- premature async/distributed complexity

---

### 5. Build the smallest useful loop
When choosing between breadth and completeness, prefer completing the minimal end-to-end loop:

1. load one skill
2. load one agent
3. load one workflow
4. execute one run
5. write one log
6. optionally emit one lesson

Do not build broad surfaces before that loop works.

---

## Current Priorities

When adding or changing code, bias toward these priorities:

### Priority 1: Repository structure
Establish and preserve a clean top-level layout:
- `skills/`
- `agents/`
- `workflows/`
- `logs/`
- `lessons/`
- `packages/`
- `apps/`

### Priority 2: Skill loading
Implement minimal support for discovering and reading `SKILL.md`.

Do not over-parse unless needed.  
Start with a simple metadata extraction approach.

### Priority 3: Agent execution
Implement a basic agent runner that can:
- load an agent definition
- attach skills
- execute a single task
- return a structured result

A stubbed execution path is acceptable early if it preserves interfaces.

### Priority 4: Run registry
Every execution should produce a durable run record on disk.

### Priority 5: Logging
Every run should produce a simple log artifact.

### Priority 6: Lessons
Support a minimal path for promoting a log/run insight into a lesson artifact.

---

## Non-Goals for Early Versions

Do not drift into these unless explicitly needed:

- rich web UI
- general-purpose chat interface
- multi-tenant auth system
- distributed orchestration platform
- remote execution dependency
- automatic memory system
- vector database requirement
- dynamic skill marketplace
- full Kubernetes dependency for MVP

---

## Kubernetes and Runtime Guidance

This project may later support k3d/k3s or Kubernetes-based execution.

Important:
- an **agent is not a pod**
- a **pod/job is one execution instance of an agent**
- runtime-specific execution details should not leak into `SKILL.md`

If runtime config is needed, put it in:
- `agent.yaml` for agent/runtime defaults
- `molt.yaml` for workflow/execution config

Do not put k8s scheduling or pod metadata into `SKILL.md`.

---

## File and Schema Guidance

### `SKILL.md`
Use as the canonical skill format.

Do not replace it with a custom skill schema.

A skill folder may include supporting files, but `SKILL.md` is the anchor.

### `agent.yaml`
Use for agent definition concerns such as:
- name
- model
- skills
- tools
- context policy
- runtime hints

### `molt.yaml`
Use for workflow concerns such as:
- workflow name
- entry agent
- inputs
- schedule
- logging policy
- execution policy

Keep boundaries clean.

---

## Coding Preferences

### Language
Prefer Python for runtime code unless there is a strong reason otherwise.

### Style
- use clear names
- add concise comments where helpful
- keep functions focused
- avoid giant files
- keep side effects explicit

### Dependencies
Add dependencies sparingly.

Before introducing a library, prefer asking:
- can the standard library do this?
- does this simplify the core loop?
- is this needed right now?

---

## Testing Guidance

Favor practical tests around the core loop.

Useful early tests:
- skill discovery works
- agent definition loads
- workflow definition loads
- running a workflow emits a run record
- running a workflow writes a log
- lesson promotion writes the expected artifact

Prefer a few strong tests over many shallow tests.

---

## When Making Changes

When working in this repo:

1. preserve the separation of skill / agent / workflow
2. keep outputs on disk and inspectable
3. keep local execution easy
4. avoid turning the system into a chat app
5. prefer minimal, end-to-end working behavior
6. leave the codebase simpler than you found it

If there is ambiguity, choose the path that best supports:
**Run → Log → Lesson → Skill → Better Run**

---

## Suggested Initial Layout

\`\`\`
skills/
  repo-triage/
    SKILL.md

agents/
  triage-worker/
    agent.yaml

workflows/
  manual-triage/
    molt.yaml

logs/
lessons/
packages/
apps/
\`\`\`

---

## First Milestone

The first milestone is complete when the repository can:

- discover one skill
- load one agent
- load one workflow
- execute one run from CLI
- write one run record
- write one log entry

Anything beyond that is secondary until this works.

---

## Notes for Agentic Coding Tools

When generating code for this repo:

- do not introduce unnecessary architecture
- do not generalize too early
- do not replace file-based state with a database
- do not build UI before the execution loop works
- do not merge skill/agent/workflow concepts
- do produce small, runnable increments
- do prefer explicit scaffolding over speculative completeness

If unsure, scaffold the simplest implementation that preserves the intended architecture.
