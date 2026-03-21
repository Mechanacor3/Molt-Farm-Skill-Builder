# Molt Farm Skill Builder

Molt Farm Skill Builder is a local-first workspace for recursively improving `SKILL.md` capabilities.

The repo is intentionally narrower now:

- evaluate strong upstream skills
- extract reusable lessons
- refine local skills
- measure whether the skill actually got better

The core loop is:

**Test -> Observe -> Lesson -> Improve -> Measure**

## What This Repo Is

This repo is primarily about skill quality, not general agent orchestration.

The most important artifacts are:

- `skills/` for reusable `SKILL.md` capabilities
- `lessons/` for distilled improvements
- `logs/` and `runs/` for inspectable evidence
- `packages/` for the minimal runtime that supports the loop

Some older agent/workflow scaffolding still exists because it is useful as local execution machinery, but it is no longer the product center.

## Current Focus

The project exists to:

- study high-quality skills from OpenAI, Anthropic, and `agentskills`
- preserve the best patterns in local reusable skills
- run evals against concrete prompts and artifacts
- compare baselines and measure whether a refinement helped
- keep the whole process local, inspectable, and file-based

## CLI Shape

The default interface is:

```bash
molt skill-builder [options]
```

Today the main paths are:

```bash
./molt skill-builder run <workflow> --input key=value
./molt skill-builder eval-skill <skill>
```

Older top-level command forms may still exist as compatibility paths, but the intended shape is the `skill-builder` namespace.

## Quick Start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
./molt skill-builder eval-skill run-summarizer
```

After a run, inspect:

- `runs/`
- `logs/YYYY-MM-DD/`
- `lessons/`
- `skills/<skill>/evals/workspace/iteration-N/`

## Design Bias

Molt Farm Skill Builder prefers:

- local-first execution
- least-context by default
- plain files over hidden state
- strong eval loops over intuition
- small, composable skills over broad abstractions

For repo-specific working guidance, see [AGENTS.md](/mnt/d/moltfarm_v2/AGENTS.md).
