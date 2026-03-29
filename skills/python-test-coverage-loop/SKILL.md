---
name: python-test-coverage-loop
description: Run, extend, or improve tests and coverage in a local Python repo. Use when Codex needs concrete `pytest`, `uv run`, or `pip install -e ".[test]"` commands, when helper-heavy modules need targeted coverage increases, or when lightweight CLI and analyzer changes need narrow test design instead of broad end-to-end sprawl.
---

# Python Test Coverage Loop

Use this skill when:
- A local Python repo needs explicit, repeatable test or coverage commands.
- Coverage is low in helper-heavy modules and the right next test shape is unclear.
- Lightweight CLI or analyzer changes need targeted tests that stay local-first and inspectable.

Instructions:
1. Start with the smallest files that define the test loop: `pyproject.toml`, the target module, nearby tests, and any directly relevant lesson files.
2. Prefer an explicit local tool path instead of assuming `pytest` is globally installed.
   - Use `pip install -e ".[test]"` when the repo exposes a test extra.
   - Otherwise use `uv run --with pytest ...` and `uv run --with pytest --with pytest-cov ...`.
3. When the prompt clearly refers to this repo, use the repo command contract exactly instead of drifting to generic shortcuts.
   - Installed path:
     - `python -m pip install -e ".[test]"`
     - `python -m pytest tests`
     - `python -m pytest tests --cov=moltfarm --cov-report=term-missing`
     - `python -m pytest tests --cov=moltfarm --cov-report=html`
   - Ad hoc path:
     - `uv run --with pytest python -m pytest tests`
     - `uv run --with pytest --with pytest-cov python -m pytest tests --cov=moltfarm --cov-report=term-missing`
     - `uv run --with pytest --with pytest-cov python -m pytest tests --cov=moltfarm --cov-report=html`
   - Do not replace these with `pytest`, `uvx`, omitted `tests`, or `--cov=.` when the repo and measured package are known.
4. Prefer repo-local pytest and coverage defaults in `pyproject.toml` so repeated commands stay short and predictable. Add or repair those defaults when they represent stable project behavior.
5. Run the narrowest useful verification first, then expand only if needed.
   - Start with a focused `python -m pytest ...` target.
   - Use `--cov=<package> --cov-report=term-missing` to find missing lines.
   - Use `--cov-report=html` when a browsable report will speed review, then inspect `htmlcov/index.html`.
6. Prefer exact commands and brief reasoning when the prompt asks for how to run tests or coverage. Do not expand into generic alternatives, placeholder package names, or large implementation sketches unless the user asks for them.
7. Raise coverage primarily with direct helper tests and a few thin dispatch tests.
   - Prefer small file-backed fixtures and direct assertions for normalization, validation, import, and path-handling branches.
   - Keep end-to-end tests only for orchestration seams that truly need broader setup.
8. When the change touches lightweight CLI code, keep optional or heavy imports lazy so parser, `--help`, and narrow command tests can run without the full runtime dependency set. Say this explicitly, not indirectly.
9. When the change touches analyzer or reporting code, preserve one discovered record per source artifact during analysis, and treat zero findings as a successful analyzed run if the command still writes an inspectable artifact.
10. State the exact command to run, the next artifact path to inspect, and any verification gaps that remain.
11. Load `@./references/repo-test-coverage-checklist.md` when you need repo-specific command shapes and heuristics.
12. Stay in the testing and coverage lane. Use `python-build` for packaging or bootstrap work, and use the repo's skill-authoring skills when the main task is creating or refining eval suites.
