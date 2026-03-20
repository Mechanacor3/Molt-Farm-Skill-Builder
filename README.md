# Molt Farm v2

Molt Farm v2 is a local-first control plane for running agent workflows, recording what happened, and improving behavior over time through reusable `SKILL.md` capabilities.

The core loop is:

**Run -> Log -> Lesson -> Skill -> Better Run**

## What This Repo Is

Molt Farm separates a few concerns cleanly:

- `skills/` holds portable capabilities anchored by `SKILL.md`
- `agents/` holds worker definitions that load skills and execution defaults
- `workflows/` holds runnable jobs that bind inputs to an agent
- `runs/` holds durable execution records
- `logs/` holds append-only records of what happened
- `lessons/` holds distilled improvements that can be promoted into skills
- `packages/` holds the minimal Python runtime
- `apps/` holds future service entrypoints

This is intentionally not a chat app, not a UI project, and not a distributed platform. The focus is local execution, inspectable files, and a tight improvement loop.

## Current Shape

Today the repo provides:

- skill discovery and loading from `SKILL.md`
- agent and workflow loading from YAML
- a CLI entrypoint via `molt run <workflow>`
- OpenAI Agents SDK execution with local-first defaults
- durable run records and per-run logs on disk
- a path for evolving skills through lessons and refinements

## Why It Exists

Most agent tooling focuses on conversation surfaces or orchestration first. Molt Farm focuses on reusable skills first.

The long-term value of the system is not just the runtime. It is the library of high-quality, narrow, composable skills that emerge from real runs and real logs.

## Quick Start

Create a virtual environment, install the package, set `OPENAI_API_KEY`, and run a workflow:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
./molt run manual-triage --input target=.
```

After a run, inspect:

- `runs/` for the structured execution record
- `logs/YYYY-MM-DD/` for the append-only log entry

## Design Bias

Molt Farm prefers:

- local-first execution
- least-context by default
- plain files over hidden state
- small, boring runtime code
- skills that are portable and composable

If you want implementation guidance and project conventions, start with [AGENTS.md](/mnt/d/moltfarm_v2/AGENTS.md).
