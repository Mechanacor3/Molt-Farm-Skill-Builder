# Docker Smoke Test Checklist

- Prefer one narrow verification target:
  - CLI help output
  - import success
  - one test command
  - one workflow command
- Reuse an existing image if the prompt already gives one.
- Use `docker build` only when the image is part of what needs verification.
- Default to `docker run --rm`.
- Add `-v "$PWD:/app" -w /app` only when the container should read live repo files or write artifacts back to the host.
- If the container should write files back to the host, prefer `--user "$(id -u):$(id -g)"`.
- Prefer one explicit post-run inspection target:
  - `stdout`
  - `runs/<id>.json`
  - `logs/YYYY-MM-DD/<id>.log`
  - `skills/<skill>/evals/workspace/iteration-N/...`
- If credentials are required, say so plainly instead of pretending the smoke test is self-contained.
