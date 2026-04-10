# Workflow-First System Map From Lessons

Source:
- runtime: `packages/moltfarm/wiki_system_map.py`
- CLI surface: `packages/moltfarm/cli.py`
- operation registry: `packages/moltfarm/operations.py`
- retrieval hooks: `packages/moltfarm/eval_authoring.py`, `packages/moltfarm/runner.py`
- validation method: `tests/test_wiki_system_map.py`, `tests/test_runner.py`, `tests/test_eval_authoring.py`

## Draft-Then-Promote Knowledge Layer Lesson

- `lesson`: Curated knowledge layers should write a reviewable draft workspace before they touch canonical wiki pages or promoted indexes.
- `evidence`: The new `manual-system-map-draft` flow writes `plan.md`, candidate pages, and a draft `lesson-index.json` under `wiki/drafts/session-N/`, while promotion is a separate `promote-system-map` step.
- `scope`: repo knowledge capture workflows
- `reuse`: When adding a new synthesis surface in Molt, keep the first pass additive and inspectable so raw evidence stays untouched until the curated layer is reviewed.

## Structured Retrieval Lesson

- `lesson`: A promoted knowledge index should preserve supporting file paths so authoring and refinement flows can retrieve the right raw lesson even when the lesson prose is generic.
- `evidence`: The promoted `wiki/_build/lesson-index.json` now stores `supporting_paths`, and both authoring and refinement lookups consult that index before falling back to raw lesson-file substring matching.
- `scope`: lesson retrieval for authoring and refinement
- `reuse`: When a curated knowledge layer drives retrieval, store the raw lesson path plus enough structured references to route context without re-reading the whole corpus every time.
