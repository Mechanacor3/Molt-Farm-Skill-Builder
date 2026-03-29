# Repo Test Coverage Checklist

This checklist folds in lessons from:
- `lessons/2026-03-28-python-test-and-coverage-entrypoints.md`
- `lessons/2026-03-28-targeted-helper-tests-for-coverage.md`
- `lessons/2026-03-28-skill-near-dupe-scanner.md`

## Command Paths

Use this repo contract exactly when the prompt is about this repository:
- `python -m pip install -e ".[test]"`
- `python -m pytest tests`
- `python -m pytest tests --cov=moltfarm --cov-report=term-missing`
- `python -m pytest tests --cov=moltfarm --cov-report=html`
- `uv run --with pytest python -m pytest tests`
- `uv run --with pytest --with pytest-cov python -m pytest tests --cov=moltfarm --cov-report=term-missing`
- `uv run --with pytest --with pytest-cov python -m pytest tests --cov=moltfarm --cov-report=html`
- Inspect `htmlcov/index.html` after the HTML coverage run.

Avoid generic substitutions when the repo is known:
- Do not switch to `pytest` in place of `python -m pytest`.
- Do not switch to `uvx` in place of `uv run --with ...`.
- Do not drop the `tests` target.
- Do not switch `--cov=moltfarm` to `--cov=.`.

Use the installed path when the repo already exposes test tooling:
- `pip install -e ".[test]"`
- `python -m pytest tests`
- `python -m pytest tests --cov=moltfarm --cov-report=term-missing`
- `python -m pytest tests --cov=moltfarm --cov-report=html`
- Inspect `htmlcov/index.html` after the HTML coverage run.

Use the ad hoc path when the user does not want to install test tooling into the active environment:
- `uv run --with pytest python -m pytest tests`
- `uv run --with pytest --with pytest-cov python -m pytest tests --cov=moltfarm --cov-report=term-missing`
- `uv run --with pytest --with pytest-cov python -m pytest tests --cov=moltfarm --cov-report=html`

## Coverage Heuristics

- Prefer direct helper tests plus a few thin dispatch tests before reaching for more end-to-end setup.
- Use small file-backed fixtures for validation, normalization, import, and path branches.
- Keep end-to-end tests for orchestration seams that cannot be exercised directly.
- Prefer stable pytest and coverage defaults in `pyproject.toml` over repeating long shell flags in every command.

## CLI And Analyzer Heuristics

- Import optional or heavy command handlers lazily inside the CLI execution branch that needs them.
- Preserve one discovered `SKILL.md` record per artifact while analyzing a skill corpus; only collapse to unique names later if the caller truly needs it.
- Treat "zero findings" as a successful analyzer run when the heuristic is allowed to return nothing and the command still writes an inspectable artifact.
