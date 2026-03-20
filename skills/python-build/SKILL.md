---
name: python-build
description: Build, bootstrap, repair, or structure a local Python project using clear packaging, virtualenvs, tests, and CLI entrypoints. Use when the user wants to scaffold Python code, fix Python build/setup issues, or make a Python repo runnable locally.
---

# Python Build

Use this skill when:
- A local Python project needs to be created, bootstrapped, or repaired.
- The user wants packaging, dependency, test, or CLI structure for Python.
- The work should stay local-first, inspectable, and simple.

Instructions:
1. Start by identifying the current Python project shape from the smallest relevant files:
   `pyproject.toml`, `requirements*.txt`, test files, and entrypoints.
2. Prefer `pyproject.toml` as the source of truth when it exists.
3. Prefer a local virtual environment and explicit dependency installation over system-wide changes.
4. Keep the implementation boring:
   - small modules
   - explicit entrypoints
   - focused tests
   - minimal dependencies
5. When scaffolding or repairing, cover these concerns in order:
   - packaging or project metadata
   - dependency install path
   - CLI or runnable entrypoint
   - test command
   - local verification step
6. If something is missing, state the smallest missing file or command needed instead of guessing.
7. Keep recommendations concrete and Python-specific. Avoid generic software-process advice.
8. Use this checklist when helpful: @./references/python-build-checklist.md
