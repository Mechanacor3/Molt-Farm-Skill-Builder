---
name: python-pytest-essentials
description: Compact practical pytest guidance for Python tests. Use when writing or reviewing Python tests and you need concise patterns for TDD, parametrization, fixtures, monkeypatch or tmp_path isolation, async pytest, and meaningful coverage advice.
---

# Python Pytest Essentials

Use this skill when:
- Writing or reviewing Python tests with pytest.
- A test question needs a narrow recommendation, not a long testing handbook.
- The work involves TDD, parametrization, fixtures, env or file isolation, async tests, or coverage guidance.

Instructions:
1. Stay compact and practical. Prefer one recommended pattern plus a small example over a broad survey of pytest features.
2. Match the test shape to the code under test:
   - pure helpers: direct unit tests
   - repeated input tables: `@pytest.mark.parametrize`
   - shared setup across modules: fixtures in `conftest.py`
   - environment or file side effects: `monkeypatch` and `tmp_path`
   - async code: `pytest-asyncio`, `@pytest.mark.asyncio`, and awaited calls
3. When asked about workflow, recommend TDD in strict order: Red, Green, Refactor.
   - Write the failing test first.
   - Add the smallest implementation that makes it pass.
   - Refactor only after the test is green.
4. Prefer one focused test with explicit inputs and assertions over many near-duplicate tests.
5. Keep fixtures small and explicit.
   - Put cross-module fixtures in `conftest.py`.
   - Mention fixture scope only when it matters for reuse or cost.
6. Avoid real environment state and repository files in narrow tests.
   - Use `monkeypatch` for env variables and attributes.
   - Use `tmp_path` for isolated file writes.
7. For async pytest guidance, recommend only the minimum setup needed:
   - `pytest-asyncio` when async support is needed
   - `@pytest.mark.asyncio` on async tests
   - async fixtures only when shared async setup is actually needed
8. For coverage guidance, treat `pytest-cov` or `pytest --cov` as measurement tooling, not the goal.
   - Prioritize risky and critical paths.
   - Do not recommend chasing a raw percentage everywhere.
9. Do not drift into CI pipelines, database harnesses, or broad plugin catalogs unless the user explicitly asks.
10. Load `@./references/pytest-practical-checklist.md` when you need concise examples or reminder patterns.
