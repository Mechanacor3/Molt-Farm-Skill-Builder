# Run Summary Template

- `attempted`: what the run was trying to do
- `happened`: what actually happened, using only the strongest facts
- `status`: `completed`, `failed`, or `partial`
- `produced`: outputs, artifacts, or notable results
- `gaps`: the main missing validation, uncertainty, or unverified assumption
- `next_step`: the single most relevant follow-up, if any

Example shape:

- `attempted`: Assess the repo's packaging setup and identify the next build step.
- `happened`: Read `pyproject.toml` and the run output. Confirmed the console entrypoint and package discovery settings, but did not run install or tests.
- `status`: completed
- `produced`: A written packaging assessment and concrete next actions; no files changed.
- `gaps`: No live build or import verification was performed.
- `next_step`: Install the project in a virtualenv and run the CLI smoke test.
