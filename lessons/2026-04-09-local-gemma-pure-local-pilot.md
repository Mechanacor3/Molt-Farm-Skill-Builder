# Local Gemma Pure-Local Pilot Lessons

Source:
- runtime: `packages/moltfarm/runner.py`
- proxy: `Molt-Farm-Proxy/app/main.py`
- proxy client: `Molt-Farm-Proxy/app/ollama_client.py`
- proxy translator: `Molt-Farm-Proxy/app/translator.py`
- direct subject runs: `runs/run-20260409154753-fbed538b.json`, `runs/run-20260409154836-6b56830b.json`, `runs/run-20260409154924-8dbfc996.json`
- proxy subject runs: `runs/run-20260409155251-78d42f66.json`, `runs/run-20260409155344-bc13de27.json`, `runs/run-20260409155431-2412f6d9.json`
- proxy logs: `Molt-Farm-Proxy/.molt-logs/proxy-requests.jsonl`
- validation method: local Gemma `llama.cpp` server on `127.0.0.1:8080`, local proxy on `127.0.0.1:8000`, full pytest suites, direct and proxy skill smoke runs

## Direct-First Lesson

- `lesson`: For a local-model pilot, make direct chat-completions the baseline path and treat proxy-backed Responses as a second surface.
- `evidence`: Gemma worked immediately on the direct `llama.cpp` surface for `get_weather`, the full `exec_command` capability probe, and the three basic skill runs, while the proxy path required additional compatibility fixes before the same workflows passed.
- `scope`: local model integration strategy
- `reuse`: When adding a new local backend, prove the direct OpenAI-compatible chat path first, then layer a Responses proxy on top only after tool calling is already known-good.

## Proxy Health And Auth Lesson

- `lesson`: A local Responses proxy must handle authenticated upstreams explicitly and expose the health contract the caller expects.
- `evidence`: The first proxy attempts failed until the proxy accepted `MOLT_UPSTREAM_API_KEY`, forwarded upstream auth, and exposed `/health` in addition to `/healthz`, while the runtime also had to treat `GET /v1/responses` returning `405` as a healthy Responses preflight.
- `scope`: proxy compatibility with local OpenAI-compatible servers
- `reuse`: When fronting an authenticated local model server, wire explicit upstream auth and support both health aliases before debugging higher-level tool behavior.

## Untyped Responses Input Lesson

- `lesson`: The OpenAI Responses client may send message items as plain `{"role": ..., "content": ...}` objects inside list input, so a proxy cannot assume every item has an explicit `"type"`.
- `evidence`: The first real `openai_responses` workflow failed with a proxy `500` because the translator only accepted typed items; normalizing role/content pairs into `type="message"` fixed the failure and allowed the `manual-triage`, `manual-run-summary`, and `manual-docker-smoke-test` workflows to complete.
- `scope`: Responses API translation
- `reuse`: Accept the SDK-style untyped message shape and convert any remaining input-shape errors into structured `400` responses instead of leaking internal server errors.

## Basic-Skill Pilot Lesson

- `lesson`: Small text-only skills are sufficient to validate a local model’s practical skill path before attempting full eval loops or local grading.
- `evidence`: Both direct and proxy-backed subject runs showed `function_call:activate_skill:*` and `function_call:read_skill_resource:*` for `repo-triage`, `run-summarizer`, and `docker-smoke-test`, while full local grading remained out of scope.
- `scope`: local skill smoke testing
- `reuse`: Start local-model validation with narrow text-only skills and judge success from trace artifacts first; do not block the pilot on local evaluator grading.
