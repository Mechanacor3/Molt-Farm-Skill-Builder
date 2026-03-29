# Python Test And Coverage Entry Points Lessons

Source:
- packaging: `pyproject.toml`
- docs: `README.md`
- validation method: local `uv run` test and coverage runs

## Test Tooling Lesson

- `lesson`: Keep local Python test tooling behind an explicit repo install path instead of assuming `pytest` is globally available.
- `evidence`: The repo now exposes a `test` extra with `pytest` and `pytest-cov`, while the README also preserves ad hoc `uv run --with ...` commands for one-off runs.
- `scope`: local developer ergonomics
- `reuse`: When a repo depends on non-runtime Python tools, expose them through a named extra or similarly explicit install path and document the exact command that uses them.

## Coverage Config Lesson

- `lesson`: Put stable test discovery and coverage defaults in `pyproject.toml` so local commands stay short and predictable.
- `evidence`: `tool.pytest.ini_options` now anchors collection to `tests/`, and `tool.coverage.*` defines `moltfarm` as the measured source with missing-line reporting enabled.
- `scope`: Python test configuration
- `reuse`: Prefer repo-local configuration over ad hoc shell flags when the goal is repeatable test and coverage behavior for every contributor.
