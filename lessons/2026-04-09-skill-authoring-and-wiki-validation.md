# Skill Authoring And Wiki Validation Lessons

Source:
- new skills: `skills/molt-skill-builder-authoring/` and `skills/llm-wiki/`
- CLI surface: `packages/moltfarm/cli.py`
- eval authoring runtime: `packages/moltfarm/eval_authoring.py`
- skill evaluator runtime: `packages/moltfarm/skill_evaluator.py`
- create-evals draft evidence: `skills/molt-skill-builder-authoring/evals/workspace/create-evals/session-1/analysis/probe-observations.json`
- partial authoring eval evidence: `skills/molt-skill-builder-authoring/evals/workspace/iteration-1/eval-start-new-skill-loop/with_skill/result.json`
- partial authoring summary: `skills/molt-skill-builder-authoring/evals/workspace/iteration-1/eval-start-new-skill-loop/with_skill/outputs/summary.txt`
- validation method: local skill loading, `uv` pytest pass, cloud-backed `create-evals` attempt, and fully local Gemma `eval-skill` attempts on `127.0.0.1:8080`

## Manual-First Eval Lesson

- `lesson`: New skills still need hand-authored canonical evals as a first-class path because `create-evals` can be blocked by external quota or probe-runtime failures.
- `evidence`: `./molt skill-builder create-evals molt-skill-builder-authoring` wrote a reviewable `session-1` workspace but failed on repeated `429 insufficient_quota`, and its `probe-primary-task` observation also recorded an `OSError: [Errno 36] File name too long` failure in `probe-observations.json`.
- `scope`: skill authoring workflow
- `reuse`: Author `SKILL.md`, fixtures, and canonical `evals/evals.json` directly first; treat `create-evals` as an additive drafting aid rather than the only route to a shippable skill.

## Local Grader Schema Lesson

- `lesson`: A local `openai_compatible` model can drive subject runs, but full `eval-skill` still needs a grader that emits the repo's exact `GradingPayload` summary schema or a normalization layer in front of it.
- `evidence`: Local Gemma completed subject outputs for both new skills, but both `eval-skill` runs failed when the local grader returned JSON without `summary.passed`, `summary.failed`, `summary.total`, and `summary.pass_rate`.
- `scope`: local evaluator grading
- `reuse`: Keep a cloud grader or add schema normalization before claiming a fully local `eval-skill` loop.

## Grader-Fallback Lesson

- `lesson`: Invalid local grader payloads should downgrade the affected checks to failed grading instead of aborting the whole eval iteration.
- `evidence`: After normalizing alternate summary keys and adding an error fallback in `packages/moltfarm/skill_evaluator.py`, the local `llm-wiki-validator` suite completed and wrote `benchmark.json`, `feedback.json`, and per-case `comparison.json` even though local grader outputs still varied in shape.
- `scope`: eval runtime resilience
- `reuse`: When local models are part of the grading path, preserve inspectable iteration artifacts by turning malformed grader output into explicit failed assertions rather than a fatal exception.

## Short-Step Authoring Lesson

- `lesson`: Authoring-loop skills need an explicit "short ordered actions and commands" instruction to keep local-model responses operational instead of essay-like.
- `evidence`: The first local subject output for `molt-skill-builder-authoring` got the sequence right but expanded into headings and narrative in `iteration-1/.../outputs/summary.txt`, which led to a follow-up tightening of the skill instructions.
- `scope`: skill instruction phrasing
- `reuse`: When evals expect concise workflow guidance, tell the skill to answer as a short ordered sequence of actions and commands.

## Source-Path Wiki Lesson

- `lesson`: Wiki-building skills should require page-level update plans to name the exact supporting note, reference, or errata path for each non-obvious fact.
- `evidence`: The partial local grading trace for `llm-wiki` passed the routing and structure checks but missed the evidence-linking check because the plan named the destination pages without explicitly tying each step back to the raw-fragment source.
- `scope`: wiki skill instruction design
- `reuse`: When a skill proposes wiki updates, require the destination page and supporting source path in the same step so evidence discipline survives summarization.
