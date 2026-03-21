---
name: docker-smoke-test
description: Propose a narrow Docker build-and-run smoke test for a local project or artifact. Use when the goal is to verify one thing inside a sandboxed container with exact commands and minimal scope.
---

# Docker Smoke Test

Use this skill when:
- A task should be verified inside Docker instead of the host environment.
- You need the first narrow container check for a Dockerfile, image, CLI, import path, or test command.
- The user wants exact `docker build` and `docker run` commands plus the main artifact or output to inspect.

Instructions:
1. Start from the smallest relevant context: the Dockerfile, the target command, and the one thing being verified.
2. Prefer one narrow smoke test over a broad validation pass.
3. If the image does not exist yet, give one exact `docker build` command. If the prompt already names an image, reuse it instead of rebuilding.
4. Give one exact `docker run` command that verifies the requested behavior.
5. Default to `--rm` and a focused working directory. Add bind mounts only when the run needs live repo files or should write artifacts back to the host.
6. When host-visible outputs matter, use a concrete bind mount such as `-v "$PWD:/app" -w /app`. If the container should write files back to the host, include `--user "$(id -u):$(id -g)"` by default unless the prompt clearly says ownership does not matter.
7. Keep environment passing narrow. Only mention `--env`, extra ports, or additional mounts when the task clearly requires them.
8. Do not drift into compose files, orchestration, CI design, or production deployment unless the user explicitly asks.
9. Produce exactly these sections in this order:
   Goal: one sentence naming the single thing the container run should verify.
   Build: one exact command or `none` if an existing image should be reused.
   Run: one exact `docker run` command.
   Verify: one or two short checks the command proves.
   Inspect: the main output, path, or signal to inspect after the run; use `stdout` if no file artifact should exist and a host path if the run should write artifacts back.
10. When helpful, use `@./references/docker-smoke-checklist.md` to keep the test narrow and inspectable.
