# Targeted Helper Tests For Coverage

Source:
- runtime modules: `packages/moltfarm/cli.py`, `packages/moltfarm/runner.py`, `packages/moltfarm/eval_authoring.py`, `packages/moltfarm/skill_evals.py`
- validation method: local `uv run pytest --cov=moltfarm --cov-report=term-missing --cov-report=`

## Coverage Lesson

- `lesson`: When a local-first module has broad orchestration but many pure helpers, raise coverage primarily with direct helper tests plus a few thin dispatch tests instead of forcing more large end-to-end setups.
- `evidence`: Covering CLI dispatch arms directly and testing runner/eval-authoring normalization helpers in isolation moved total coverage from `82%` to `94%` without runtime refactors or broader fixture sprawl.
- `scope`: Python test design
- `reuse`: Prefer small file-backed fixtures and direct helper assertions for validation, normalization, import, and path-handling branches; keep end-to-end tests for only the orchestration seams that actually need them.
