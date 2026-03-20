# Python Build Checklist

- Check whether `pyproject.toml` exists and what it defines.
- Check whether the repo already standardizes on `uv`, `pip`, or another installer.
- Prefer `.venv` for local execution.
- Confirm at least one runnable entrypoint and one test command.
- Add or update the smallest possible set of files to make the project runnable.
