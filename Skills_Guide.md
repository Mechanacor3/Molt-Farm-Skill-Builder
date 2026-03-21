# Skills Guide

![Skills Guide diagram](./Skills_Guide.png)

This guide distills the supplied "Technical Framework for Skill Evolution" into a practical reference for building high-value skills in this repository.

## Purpose

The shift is from one-off prompting to repeatable, inspectable agent workflows. In this repo, the unit of capability is the skill, and the governing loop is:

**Test -> Observe -> Lesson -> Improve -> Measure**

That means a good skill is not just a prompt. It is a reusable package of instructions, references, artifacts, and evidence that can be evaluated and refined over time.

## Core Principles

1. Safety first. Constrain execution, minimize exposure, and avoid unnecessary permissions, network access, or broad context.
2. Interpretability. Keep instructions, artifacts, logs, and outputs visible on disk so runs can be inspected and audited.
3. Beneficial impact. Focus on useful engineering work instead of vague chat behavior or model "vibes."
4. Local-first design. Prefer local files, local runs, and plain artifacts over hidden services or opaque state.
5. Least context by default. Load only the instructions and references needed for the task at hand.

## What A Skill Is

In this repo, the canonical unit is `SKILL.md`, not `SKILLS.md`.

A skill should be a small, focused capability with a clear trigger and a clear output. Typical structure:

- `SKILL.md`: the core instructions, trigger description, scope, and workflow
- `references/`: supporting docs, specs, examples, or domain notes
- `scripts/`: small helper scripts when plain instructions are not enough
- `assets/`: static templates, images, or example artifacts

Good skills are:

- narrow in scope
- explicit about when they should trigger
- usable with minimal prior chat history
- grounded in local references instead of broad conversational memory

## Skill Design Rules

### 1. Single responsibility

Each skill should solve one well-bounded problem well. Examples:

- evaluate a skill against a prompt suite
- extract lessons from a run
- summarize run artifacts for review
- refine a skill based on concrete eval feedback

Broad, multi-purpose skills are harder to trigger correctly and harder to measure.

### 2. Clear trigger descriptions

The description is routing metadata. It should say:

- what problem the skill solves
- what inputs it expects
- what outputs or artifacts it produces
- when it should be used instead of a general approach

### 3. Stateless execution

Assume minimal memory. A skill should work from:

- its `SKILL.md`
- explicitly loaded references
- the user prompt
- local artifacts relevant to the task

Do not depend on long conversational history unless absolutely necessary.

## Context Management

Context quality matters as much as model quality. The main practices are:

- Progressive disclosure: load the full skill only when the task matches it
- Narrow references: pass only the files needed for the current task
- Compaction: summarize prior work into durable artifacts instead of dragging full history forward
- Explicit cues: use concrete task language and examples so the right skill is selected

In practice for this repo, that means preferring eval cases, lesson files, logs, and run artifacts over broad repo dumps.

## Multi-Agent Orchestration

Parallel agents can be useful, but they are execution machinery, not the product.

Useful patterns:

- isolate parallel work in separate worktrees
- assign each agent a bounded task and write scope
- compare diffs and artifacts before merging
- keep the human reviewer in control of final integration

For Molt Farm, orchestration should support the skill loop, not overshadow it.

## Safety And Guardrails

Any system that can run commands, edit files, or call the network needs constraints.

Preferred guardrails:

- restrict work to the relevant project directories
- default to local inspection over outbound calls
- require explicit approval for sensitive actions where applicable
- block destructive or irrelevant commands
- preserve logs and artifacts for later review

The goal is not just policy compliance. The goal is preserving system integrity while keeping runs inspectable.

## Benchmarking And Model Use

Model choice should follow task shape:

- use stronger reasoning for architecture, root-cause analysis, and complex refactors
- use lighter-weight models for narrow implementation work when quality is still sufficient
- judge outputs by correctness, instruction-following, and downstream impact, not style alone

The harness should stay model-agnostic where possible so the workflow can evolve without rewriting the surrounding system.

## How This Maps To Molt Farm

This repo already aligns with the strongest parts of the framework:

- skills are first-class artifacts
- lessons are durable improvement records
- runs and logs provide inspectable evidence
- the preferred CLI is narrow and file-oriented
- the main loop is evaluation-driven rather than intuition-driven

When applying the framework here, favor:

- `skills/` for reusable capabilities
- `lessons/` for distilled findings
- `runs/` and `logs/` for evidence
- small runtime support in `packages/`

Avoid turning the repo into a general agent platform, chat surface, or orchestration-heavy runtime.

## Practical Checklist

When authoring or refining a skill, use this checklist:

1. Define one clear job for the skill.
2. Write a precise trigger description in `SKILL.md`.
3. Keep instructions inspectable and concrete.
4. Add only the references required for that job.
5. Prefer simple scripts over complex abstractions.
6. Run evals against realistic prompts or artifacts.
7. Save outputs, grading, timing, and notes to disk.
8. Promote repeated findings into lesson files.
9. Refine the skill and rerun the eval.
10. Compare results against the prior version or baseline.

## Bottom Line

High-value skills are modular, narrow, inspectable, and measurable. The best workflow is not "ask the model again." It is:

**build a skill -> evaluate it -> extract lessons -> refine it -> measure whether it improved**
