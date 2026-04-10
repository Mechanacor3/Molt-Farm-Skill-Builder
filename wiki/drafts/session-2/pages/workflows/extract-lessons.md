# Extract Lessons

How Molt distills run and eval evidence into reusable lesson files.

## Working Guidance
### Stable
- Keep the target application repo outside the skill-foundry repo and bind it through local config when the goal is to study agent behavior rather than absorb the product code. Supporting lesson: [lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md](../../../../../lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md)
  Evidence: `fishbowl/config/target.example.json` points at an external repo path, `fishbowl/.gitignore` excludes `config/target.local.json`, and both fishbowl and root docs state that the 1602-style game source does not belong in this repo.
  Reuse: When a local agent experiment needs to point at another codebase, keep the target external, gate access through local config, and preserve the host repo for prompts, evidence, and lessons.
- A long-running opencode experiment is easier to evolve and eventually extract when its config, agents, skills, and journal live under one top-level subtree. Supporting lesson: [lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md](../../../../../lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md)
  Evidence: The new fishbowl scaffold keeps `opencode.json`, `.opencode/agents/`, `.opencode/skills/`, `AGENTS.md`, and the journal files together under `fishbowl/` instead of spreading them across the main runtime paths.
  Reuse: When a repo-hosted experiment may later become a separate project or submodule, start with one self-contained top-level folder and explicit boundaries.

### Tentative
- Small text-only skills are sufficient to validate a local model’s practical skill path before attempting full eval loops or local grading. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../../../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: Both direct and proxy-backed subject runs showed `function_call:activate_skill:*` and `function_call:read_skill_resource:*` for `repo-triage`, `run-summarizer`, and `docker-smoke-test`, while full local grading remained out of scope.
  Reuse: Start local-model validation with narrow text-only skills and judge success from trace artifacts first; do not block the pilot on local evaluator grading.
- For a local-model pilot, make direct chat-completions the baseline path and treat proxy-backed Responses as a second surface. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../../../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: Gemma worked immediately on the direct `llama.cpp` surface for `get_weather`, the full `exec_command` capability probe, and the three basic skill runs, while the proxy path required additional compatibility fixes before the same workflows passed.
  Reuse: When adding a new local backend, prove the direct OpenAI-compatible chat path first, then layer a Responses proxy on top only after tool calling is already known-good.
- A local Responses proxy must handle authenticated upstreams explicitly and expose the health contract the caller expects. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../../../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: The first proxy attempts failed until the proxy accepted `MOLT_UPSTREAM_API_KEY`, forwarded upstream auth, and exposed `/health` in addition to `/healthz`, while the runtime also had to treat `GET /v1/responses` returning `405` as a healthy Responses preflight.
  Reuse: When fronting an authenticated local model server, wire explicit upstream auth and support both health aliases before debugging higher-level tool behavior.
- The OpenAI Responses client may send message items as plain `{"role": ..., "content": ...}` objects inside list input, so a proxy cannot assume every item has an explicit `"type"`. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../../../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: The first real `openai_responses` workflow failed with a proxy `500` because the translator only accepted typed items; normalizing role/content pairs into `type="message"` fixed the failure and allowed the `manual-triage`, `manual-run-summary`, and `manual-docker-smoke-test` workflows to complete.
  Reuse: Accept the SDK-style untyped message shape and convert any remaining input-shape errors into structured `400` responses instead of leaking internal server errors.
- Invalid local grader payloads should downgrade the affected checks to failed grading instead of aborting the whole eval iteration. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: After normalizing alternate summary keys and adding an error fallback in `packages/moltfarm/skill_evaluator.py`, the local `llm-wiki-validator` suite completed and wrote `benchmark.json`, `feedback.json`, and per-case `comparison.json` even though local grader outputs still varied in shape.
  Reuse: When local models are part of the grading path, preserve inspectable iteration artifacts by turning malformed grader output into explicit failed assertions rather than a fatal exception.
- A local `openai_compatible` model can drive subject runs, but full `eval-skill` still needs a grader that emits the repo's exact `GradingPayload` summary schema or a normalization layer in front of it. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: Local Gemma completed subject outputs for both new skills, but both `eval-skill` runs failed when the local grader returned JSON without `summary.passed`, `summary.failed`, `summary.total`, and `summary.pass_rate`.
  Reuse: Keep a cloud grader or add schema normalization before claiming a fully local `eval-skill` loop.
- New skills still need hand-authored canonical evals as a first-class path because `create-evals` can be blocked by external quota or probe-runtime failures. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: `./molt skill-builder create-evals molt-skill-builder-authoring` wrote a reviewable `session-1` workspace but failed on repeated `429 insufficient_quota`, and its `probe-primary-task` observation also recorded an `OSError: [Errno 36] File name too long` failure in `probe-observations.json`.
  Reuse: Author `SKILL.md`, fixtures, and canonical `evals/evals.json` directly first; treat `create-evals` as an additive drafting aid rather than the only route to a shippable skill.
- Authoring-loop skills need an explicit "short ordered actions and commands" instruction to keep local-model responses operational instead of essay-like. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: The first local subject output for `molt-skill-builder-authoring` got the sequence right but expanded into headings and narrative in `iteration-1/.../outputs/summary.txt`, which led to a follow-up tightening of the skill instructions.
  Reuse: When evals expect concise workflow guidance, tell the skill to answer as a short ordered sequence of actions and commands.
- Wiki-building skills should require page-level update plans to name the exact supporting note, reference, or errata path for each non-obvious fact. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: The partial local grading trace for `llm-wiki` passed the routing and structure checks but missed the evidence-linking check because the plan named the destination pages without explicitly tying each step back to the raw-fragment source.
  Reuse: When a skill proposes wiki updates, require the destination page and supporting source path in the same step so evidence discipline survives summarization.
- Local-model agent prompts work better when each agent owns one skill and answers in short ordered operational steps. Supporting lesson: [lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md](../../../../../lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md)
  Evidence: The fishbowl scaffold gives `overseer`, `shipwright`, `scout`, and `scribe` one matching skill each, and every fishbowl skill requires compact ordered output fields instead of broad narrative responses.
  Reuse: When testing small local agents, keep prompts short, keep responsibilities narrow, and make stop conditions explicit so the run stays observable.

## Relevant Runtime Surfaces
- [skills/lesson-extractor/SKILL.md](../../../../../skills/lesson-extractor/SKILL.md)
- [README.md](../../../../../README.md)
- [Molt-Farm-Proxy/.molt-logs/proxy-requests.jsonl](../../../../../Molt-Farm-Proxy/.molt-logs/proxy-requests.jsonl)
- [Molt-Farm-Proxy/app/main.py](../../../../../Molt-Farm-Proxy/app/main.py)
- [Molt-Farm-Proxy/app/ollama_client.py](../../../../../Molt-Farm-Proxy/app/ollama_client.py)
- [Molt-Farm-Proxy/app/translator.py](../../../../../Molt-Farm-Proxy/app/translator.py)
- [packages/moltfarm/runner.py](../../../../../packages/moltfarm/runner.py)
- [packages/moltfarm/cli.py](../../../../../packages/moltfarm/cli.py)

## Supporting Lesson Files
- [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../../../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
- [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../../../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
- [lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md](../../../../../lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md)
