# Docker Smoke Test Refinement Lessons

Source:
- skill: `skills/docker-smoke-test/SKILL.md`
- validation method: local Docker image build plus bind-mounted smoke run
- container command shape: `docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/app" -w /app ...`

## Artifact Ownership Lesson

- `lesson`: When a bind-mounted container run should write artifacts back to the host, include `--user "$(id -u):$(id -g)"` by default.
- `evidence`: The successful bind-mounted smoke run used `--user "$(id -u):$(id -g)"` so output files landed in the working tree with the host user's ownership instead of root ownership.
- `scope`: Docker smoke-test skills
- `reuse`: If a smoke test is expected to create host-visible files under a bind mount, prefer a host-user mapping unless the prompt clearly says ownership does not matter.

## Narrowness Lesson

- `lesson`: Distinguish stdout-only checks from artifact-writing checks explicitly in the output contract.
- `evidence`: The repo validation had two different container patterns: CLI help and `unittest` runs were stdout-first, while bind-mounted workflow runs were artifact-first and needed a host path to inspect.
- `scope`: container verification skills
- `reuse`: In Docker test recommendations, tell the user whether the post-run inspection target is `stdout` or a host path, and only add a bind mount when the latter is needed.

## Reuse Lesson

- `lesson`: Reuse a known-good image name when the prompt already provides one.
- `evidence`: `moltfarm-skillbuilder:verify` was enough for container smoke runs after the initial image build, so rebuilding would have added cost without improving the check.
- `scope`: Docker smoke-test skills
- `reuse`: Prefer `Build: none` when the prompt already names a usable image and the verification target is the run behavior, not the build itself.
