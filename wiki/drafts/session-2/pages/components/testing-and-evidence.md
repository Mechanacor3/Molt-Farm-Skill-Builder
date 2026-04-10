# Testing And Evidence

How tests, traces, and file-backed artifacts validate changes without hiding the evidence.

## Working Guidance
### Stable
- Keep the target application repo outside the skill-foundry repo and bind it through local config when the goal is to study agent behavior rather than absorb the product code. Supporting lesson: [lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md](../../../../../lessons/2026-04-10-fishbowl-scaffold-for-local-opencode.md)
  Evidence: `fishbowl/config/target.example.json` points at an external repo path, `fishbowl/.gitignore` excludes `config/target.local.json`, and both fishbowl and root docs state that the 1602-style game source does not belong in this repo.
  Reuse: When a local agent experiment needs to point at another codebase, keep the target external, gate access through local config, and preserve the host repo for prompts, evidence, and lessons.

### Tentative
- Small text-only skills are sufficient to validate a local model’s practical skill path before attempting full eval loops or local grading. Supporting lesson: [lessons/2026-04-09-local-gemma-pure-local-pilot.md](../../../../../lessons/2026-04-09-local-gemma-pure-local-pilot.md)
  Evidence: Both direct and proxy-backed subject runs showed `function_call:activate_skill:*` and `function_call:read_skill_resource:*` for `repo-triage`, `run-summarizer`, and `docker-smoke-test`, while full local grading remained out of scope.
  Reuse: Start local-model validation with narrow text-only skills and judge success from trace artifacts first; do not block the pilot on local evaluator grading.
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

## Relevant Runtime Surfaces
- [README.md](../../../../../README.md)
- [tests](../../../../../tests)
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
