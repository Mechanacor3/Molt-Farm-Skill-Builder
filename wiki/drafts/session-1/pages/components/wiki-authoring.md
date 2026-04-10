# Wiki Authoring

The evidence discipline and taxonomy rules for turning notes into curated wiki pages.

## Working Guidance
### Stable
- A promoted knowledge index should preserve supporting file paths so authoring and refinement flows can retrieve the right raw lesson even when the lesson prose is generic. Supporting lesson: [lessons/2026-04-09-workflow-first-system-map-from-lessons.md](../../../../../lessons/2026-04-09-workflow-first-system-map-from-lessons.md)
  Evidence: The promoted `wiki/_build/lesson-index.json` now stores `supporting_paths`, and both authoring and refinement lookups consult that index before falling back to raw lesson-file substring matching.
  Reuse: When a curated knowledge layer drives retrieval, store the raw lesson path plus enough structured references to route context without re-reading the whole corpus every time.

### Tentative
- Invalid local grader payloads should downgrade the affected checks to failed grading instead of aborting the whole eval iteration. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: After normalizing alternate summary keys and adding an error fallback in `packages/moltfarm/skill_evaluator.py`, the local `llm-wiki-validator` suite completed and wrote `benchmark.json`, `feedback.json`, and per-case `comparison.json` even though local grader outputs still varied in shape.
  Reuse: When local models are part of the grading path, preserve inspectable iteration artifacts by turning malformed grader output into explicit failed assertions rather than a fatal exception.
- A local `openai_compatible` model can drive subject runs, but full `eval-skill` still needs a grader that emits the repo's exact `GradingPayload` summary schema or a normalization layer in front of it. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: Local Gemma completed subject outputs for both new skills, but both `eval-skill` runs failed when the local grader returned JSON without `summary.passed`, `summary.failed`, `summary.total`, and `summary.pass_rate`.
  Reuse: Keep a cloud grader or add schema normalization before claiming a fully local `eval-skill` loop.
- New skills still need hand-authored canonical evals as a first-class path because `create-evals` can be blocked by external quota or probe-runtime failures. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: `./molt skill-builder create-evals molt-skill-builder-authoring` wrote a reviewable `session-1` workspace but failed on repeated `429 insufficient_quota`, and its `probe-primary-task` observation also recorded an `OSError: [Errno 36] File name too long` failure in `probe-observations.json`.
  Reuse: Author `SKILL.md`, fixtures, and canonical `evals/evals.json` directly first; treat `create-evals` as an additive drafting aid rather than the only route to a shippable skill.
- Authoring-loop skills need an explicit "short ordered actions and commands" instruction to keep local-model responses operational instead of essay-like. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: The first local subject output for `molt-skill-builder-authoring` got the sequence right but expanded into headings and narrative in `iteration-1/.../outputs/summary.txt`, which led to a follow-up tightening of the skill instructions.
  Reuse: When evals expect concise workflow guidance, tell the skill to answer as a short ordered sequence of actions and commands.
- Wiki-building skills should require page-level update plans to name the exact supporting note, reference, or errata path for each non-obvious fact. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: The partial local grading trace for `llm-wiki` passed the routing and structure checks but missed the evidence-linking check because the plan named the destination pages without explicitly tying each step back to the raw-fragment source.
  Reuse: When a skill proposes wiki updates, require the destination page and supporting source path in the same step so evidence discipline survives summarization.
- Curated knowledge layers should write a reviewable draft workspace before they touch canonical wiki pages or promoted indexes. Supporting lesson: [lessons/2026-04-09-workflow-first-system-map-from-lessons.md](../../../../../lessons/2026-04-09-workflow-first-system-map-from-lessons.md)
  Evidence: The new `manual-system-map-draft` flow writes `plan.md`, candidate pages, and a draft `lesson-index.json` under `wiki/drafts/session-N/`, while promotion is a separate `promote-system-map` step.
  Reuse: When adding a new synthesis surface in Molt, keep the first pass additive and inspectable so raw evidence stays untouched until the curated layer is reviewed.

## Relevant Runtime Surfaces
- [skills/llm-wiki/SKILL.md](../../../../../skills/llm-wiki/SKILL.md)
- [skills/llm-wiki-validator/SKILL.md](../../../../../skills/llm-wiki-validator/SKILL.md)
- [packages/moltfarm/cli.py](../../../../../packages/moltfarm/cli.py)
- [packages/moltfarm/eval_authoring.py](../../../../../packages/moltfarm/eval_authoring.py)
- [packages/moltfarm/skill_evaluator.py](../../../../../packages/moltfarm/skill_evaluator.py)
- [skills/llm-wiki/](../../../../../skills/llm-wiki)
- [skills/molt-skill-builder-authoring/](../../../../../skills/molt-skill-builder-authoring)
- [packages/moltfarm/operations.py](../../../../../packages/moltfarm/operations.py)

## Supporting Lesson Files
- [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
- [lessons/2026-04-09-workflow-first-system-map-from-lessons.md](../../../../../lessons/2026-04-09-workflow-first-system-map-from-lessons.md)
