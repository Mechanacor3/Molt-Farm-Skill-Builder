# Local Model Pilot

How Molt validates a direct local-model path first, then layers proxy-backed surfaces and local grading carefully.

## Working Guidance

### Tentative
- Small text-only skills are sufficient to validate a local model’s practical skill path before attempting full eval loops or local grading. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: Both direct and proxy-backed subject runs showed `function_call:activate_skill:*` and `function_call:read_skill_resource:*` for `repo-triage`, `run-summarizer`, and `docker-smoke-test`, while full local grading remained out of scope.
  Reuse: Start local-model validation with narrow text-only skills and judge success from trace artifacts first; do not block the pilot on local evaluator grading.
- For a local-model pilot, make direct chat-completions the baseline path and treat proxy-backed Responses as a second surface. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: Gemma worked immediately on the direct `llama.cpp` surface for `get_weather`, the full `exec_command` capability probe, and the three basic skill runs, while the proxy path required additional compatibility fixes before the same workflows passed.
  Reuse: When adding a new local backend, prove the direct OpenAI-compatible chat path first, then layer a Responses proxy on top only after tool calling is already known-good.
- A local Responses proxy must handle authenticated upstreams explicitly and expose the health contract the caller expects. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: The first proxy attempts failed until the proxy accepted `MOLT_UPSTREAM_API_KEY`, forwarded upstream auth, and exposed `/health` in addition to `/healthz`, while the runtime also had to treat `GET /v1/responses` returning `405` as a healthy Responses preflight.
  Reuse: When fronting an authenticated local model server, wire explicit upstream auth and support both health aliases before debugging higher-level tool behavior.
- The OpenAI Responses client may send message items as plain `{"role": ..., "content": ...}` objects inside list input, so a proxy cannot assume every item has an explicit `"type"`. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: The first real `openai_responses` workflow failed with a proxy `500` because the translator only accepted typed items; normalizing role/content pairs into `type="message"` fixed the failure and allowed the `manual-triage`, `manual-run-summary`, and `manual-docker-smoke-test` workflows to complete.
  Reuse: Accept the SDK-style untyped message shape and convert any remaining input-shape errors into structured `400` responses instead of leaking internal server errors.
- Invalid local grader payloads should downgrade the affected checks to failed grading instead of aborting the whole eval iteration. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: After normalizing alternate summary keys and adding an error fallback in `packages/moltfarm/skill_evaluator.py`, the local `llm-wiki-validator` suite completed and wrote `benchmark.json`, `feedback.json`, and per-case `comparison.json` even though local grader outputs still varied in shape.
  Reuse: When local models are part of the grading path, preserve inspectable iteration artifacts by turning malformed grader output into explicit failed assertions rather than a fatal exception.
- A local `openai_compatible` model can drive subject runs, but full `eval-skill` still needs a grader that emits the repo's exact `GradingPayload` summary schema or a normalization layer in front of it. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: Local Gemma completed subject outputs for both new skills, but both `eval-skill` runs failed when the local grader returned JSON without `summary.passed`, `summary.failed`, `summary.total`, and `summary.pass_rate`.
  Reuse: Keep a cloud grader or add schema normalization before claiming a fully local `eval-skill` loop.
- Authoring-loop skills need an explicit "short ordered actions and commands" instruction to keep local-model responses operational instead of essay-like. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: The first local subject output for `molt-skill-builder-authoring` got the sequence right but expanded into headings and narrative in `iteration-1/.../outputs/summary.txt`, which led to a follow-up tightening of the skill instructions.
  Reuse: When evals expect concise workflow guidance, tell the skill to answer as a short ordered sequence of actions and commands.

## Relevant Runtime Surfaces
- [packages/moltfarm/runner.py](../../packages/moltfarm/runner.py)
- [Molt-Farm-Proxy/app/main.py](../../Molt-Farm-Proxy/app/main.py)
- [Molt-Farm-Proxy/app/translator.py](../../Molt-Farm-Proxy/app/translator.py)
- [README.md](../../README.md)
- [Molt-Farm-Proxy/.molt-logs/proxy-requests.jsonl](../../Molt-Farm-Proxy/.molt-logs/proxy-requests.jsonl)
- [Molt-Farm-Proxy/app/ollama_client.py](../../Molt-Farm-Proxy/app/ollama_client.py)
- [packages/moltfarm/cli.py](../../packages/moltfarm/cli.py)
- [packages/moltfarm/eval_authoring.py](../../packages/moltfarm/eval_authoring.py)

## Supporting Lesson Files
- [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
- [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
