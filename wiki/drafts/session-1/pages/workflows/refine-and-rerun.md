# Refine And Rerun

How Molt applies lessons back into skills, reruns the same surface, and checks whether behavior improved.

## Working Guidance
### Stable
- Refine a skill by rerunning the same concrete input before and after the edit, then compare output shape and evidence handling. Supporting lesson: [lessons/2026-03-20-run-summarizer-refinement.md](../../../../../lessons/2026-03-20-run-summarizer-refinement.md)
  Evidence: The same target run `runs/run-20260320191724-fff0f529.json` produced a looser first summary and a tighter revised summary after only the skill instructions changed.
  Reuse: When improving a skill, keep the test case fixed, change only the skill, and compare the two outputs before promoting the lesson.
- Always include a dedicated gaps field that lists unperformed verifications and unconfirmed assumptions. Supporting lesson: [lessons/2026-03-20-run-summarizer-refinement.md](../../../../../lessons/2026-03-20-run-summarizer-refinement.md)
  Evidence: The revised summary adds `gaps: No live build or import/CLI verification; existence of packages/moltfarm/cli.py was not confirmed.` while the initial summary had no explicit gaps field.
  Reuse: Require a `gaps` field in summary-style skills whenever the run may leave important checks unperformed.
- Include artifact paths and run ids where they materially improve traceability. Supporting lesson: [lessons/2026-03-20-run-summarizer-refinement.md](../../../../../lessons/2026-03-20-run-summarizer-refinement.md)
  Evidence: The revised summary names the target run id in `happened` and points to the source run record and log in `produced`.
  Reuse: When summarizing a prior run, cite the source run id and the main artifact paths if they fit cleanly in the output contract.
- Keep the field set fixed and ordered so outputs are easy to scan and compare across runs. Supporting lesson: [lessons/2026-03-20-run-summarizer-refinement.md](../../../../../lessons/2026-03-20-run-summarizer-refinement.md)
  Evidence: The revised summary uses `attempted`, `happened`, `status`, `produced`, `gaps`, `next_step` and drops the extra header and top metadata block.
  Reuse: Prefer one stable output contract per skill instead of optional headers or ad hoc metadata sections.
- Make `next_step` one concrete, low-effort verification action instead of a branching plan. Supporting lesson: [lessons/2026-03-20-run-summarizer-refinement.md](../../../../../lessons/2026-03-20-run-summarizer-refinement.md)
  Evidence: The revised summary narrows the follow-up to `pip install -e .` and `molt --help`, while the initial summary mixed layout decisions with installation and verification.
  Reuse: Prefer one immediate smoke test or validation step that the user can run without additional planning.
- State explicitly when no build, install, or file mutation happened. Supporting lesson: [lessons/2026-03-20-run-summarizer-refinement.md](../../../../../lessons/2026-03-20-run-summarizer-refinement.md)
  Evidence: The revised summary says `no files changed and no distributions built`, which is more informative than only saying no code changed.
  Reuse: In `produced`, name the absence of expected side effects when that absence changes how the output should be interpreted.
- Treat recorded run status as transport truth, not a synonym for success. Supporting lesson: [lessons/2026-03-20-run-summarizer-refinement.md](../../../../../lessons/2026-03-20-run-summarizer-refinement.md)
  Evidence: The first summary rewrote `completed` as `success (completed)`. The revised summary preserves `status: completed` and leaves outcome detail to the other fields.
  Reuse: Preserve the run's recorded status verbatim unless the system has a separate evaluated outcome field.
- When a bind-mounted container run should write artifacts back to the host, include `--user "$(id -u):$(id -g)"` by default. Supporting lesson: [lessons/2026-03-21-docker-smoke-test-refinement.md](../../../../../lessons/2026-03-21-docker-smoke-test-refinement.md)
  Evidence: The successful bind-mounted smoke run used `--user "$(id -u):$(id -g)"` so output files landed in the working tree with the host user's ownership instead of root ownership.
  Reuse: If a smoke test is expected to create host-visible files under a bind mount, prefer a host-user mapping unless the prompt clearly says ownership does not matter.
- Distinguish stdout-only checks from artifact-writing checks explicitly in the output contract. Supporting lesson: [lessons/2026-03-21-docker-smoke-test-refinement.md](../../../../../lessons/2026-03-21-docker-smoke-test-refinement.md)
  Evidence: The repo validation had two different container patterns: CLI help and `unittest` runs were stdout-first, while bind-mounted workflow runs were artifact-first and needed a host path to inspect.
  Reuse: In Docker test recommendations, tell the user whether the post-run inspection target is `stdout` or a host path, and only add a bind mount when the latter is needed.
- Reuse a known-good image name when the prompt already provides one. Supporting lesson: [lessons/2026-03-21-docker-smoke-test-refinement.md](../../../../../lessons/2026-03-21-docker-smoke-test-refinement.md)
  Evidence: `moltfarm-skillbuilder:verify` was enough for container smoke runs after the initial image build, so rebuilding would have added cost without improving the check.
  Reuse: Prefer `Build: none` when the prompt already names a usable image and the verification target is the run behavior, not the build itself.
- When exposing repo-local skills to Codex, install the repo-shaped set rather than every local skill indiscriminately. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../../../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The local Codex skill install kept `molt-cli`, `eval-author`, `lesson-extractor`, `repo-triage`, `run-summarizer`, `skill-finder`, `skill-refiner`, `python-build`, and `docker-smoke-test`, while leaving game-specific skills out of the default set.
  Reuse: Treat Codex local skill installation as part of repo ergonomics; pick the subset that matches the repo’s actual workflow and avoid unrelated clusters by default.
- For CLI command skills, pair opt-in flag cases with explicit no-flag cases. Supporting lesson: [lessons/2026-03-28-molt-cli-evals-refinement.md](../../../../../lessons/2026-03-28-molt-cli-evals-refinement.md)
  Evidence: The existing suite covered `eval-skill ... --baseline snapshot --snapshot-current`, while the new `eval-skill-basic-command` case separately exercised the opposite behavior: do not add snapshot flags when the user asked for a one-off eval.
  Reuse: When a command has optional flags that materially change behavior, add one eval that requires the flag and another that forbids it unless requested.
- Treat `grading.json` entries that say "The grader did not return a result for this check." as grader failures first, not automatic skill regressions. Supporting lesson: [lessons/2026-03-28-molt-cli-evals-refinement.md](../../../../../lessons/2026-03-28-molt-cli-evals-refinement.md)
  Evidence: In `iteration-2`, the `eval-skill-command` and `eval-skill-basic-command` outputs both contained the expected `./molt skill-builder eval-skill ...` commands and artifact paths in `result.json`, while the corresponding `grading.json` files marked every check failed only because the grader returned no assertions.
  Reuse: When an eval score looks implausibly low, inspect `result.json` alongside `grading.json` before rewriting the skill or the checks, and rerun or simplify the checks if the grader response is empty.
- Artifact-inspection evals should anchor the answer to the target skill workspace, not just to a generic current case directory. Supporting lesson: [lessons/2026-03-28-molt-cli-evals-refinement.md](../../../../../lessons/2026-03-28-molt-cli-evals-refinement.md)
  Evidence: The `eval-workspace-case-inspection` case asked about `run-summarizer`, but the with-skill output drifted toward the current eval case folder (`iteration-2/eval-eval-workspace-case-inspection/...`) instead of `skills/run-summarizer/evals/workspace/iteration-N/...`.
  Reuse: When authoring skill references or checks for inspection prompts, include the target skill name and expected `skills/<skill>/evals/workspace/...` path pattern explicitly so the response stays attached to the intended workspace.
- Any leaderboard produced before a grader-behavior change should be treated as historical, not directly comparable to post-fix runs. Supporting lesson: [lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md](../../../../../lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md)
  Evidence: The original upstream pytest bake-off highlighted Luxor and Mindrally, but the post-fix `python-pytest-essentials` run used a materially different grading path and therefore cannot be ranked fairly against those earlier numbers without rerunning them.
  Reuse: After changing grader alignment, rerun the top comparison set or explicitly label the new run as a follow-up on a changed eval surface.
- Recovering paraphrased grader outputs is necessary, but once that recovery is in place, a generic eval suite may stop separating skill quality from baseline capability. Supporting lesson: [lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md](../../../../../lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md)
  Evidence: After hardening grading alignment and rerunning the six-case pytest suite for `python-pytest-essentials`, both the with-skill and without-skill configurations scored a perfect `1.0` weighted pass rate across all six cases.
  Reuse: When a suite suddenly becomes all ties after a grader fix, treat that as evidence that the suite is saturated, not that every skill is equally good.
- A promoted knowledge index should preserve supporting file paths so authoring and refinement flows can retrieve the right raw lesson even when the lesson prose is generic. Supporting lesson: [lessons/2026-04-09-workflow-first-system-map-from-lessons.md](../../../../../lessons/2026-04-09-workflow-first-system-map-from-lessons.md)
  Evidence: The promoted `wiki/_build/lesson-index.json` now stores `supporting_paths`, and both authoring and refinement lookups consult that index before falling back to raw lesson-file substring matching.
  Reuse: When a curated knowledge layer drives retrieval, store the raw lesson path plus enough structured references to route context without re-reading the whole corpus every time.

### Tentative
- Put real regression cases behind a tracked manifest instead of relying on ad hoc manual reruns. Supporting lesson: [lessons/2026-03-28-codex-skill-system-harness.md](../../../../../lessons/2026-03-28-codex-skill-system-harness.md)
  Evidence: `tests/system/codex_skill_corpus.json` captured the concrete log paths and expected skill orders, which turned the external log corpus into a repeatable pass/fail system check.
  Reuse: For parser and trace-analysis work, track a small manifest of real cases with explicit expectations so regressions fail in a repeatable way.
- Conversational eval creation should write a reviewable draft workspace before it touches canonical `evals/` files. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../../../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The implemented `create-evals` flow writes `session.json`, probe outputs, suggested flavors, draft fixtures, and `draft/evals.json` under `skills/<skill>/evals/workspace/create-evals/session-N/`, and only promotes into canonical files on explicit `--promote`.
  Reuse: When adding authoring or refinement flows to this repo, keep the first pass additive and inspectable so the user can review artifacts before promotion.
- Separate “candidate found” from “analysis succeeded” when a conservative heuristic is intentionally allowed to return zero matches. Supporting lesson: [lessons/2026-03-28-skill-near-dupe-scanner.md](../../../../../lessons/2026-03-28-skill-near-dupe-scanner.md)
  Evidence: The real smoke run over this repo's current `skills/` tree completed successfully and wrote a report, but produced zero pairs because the planned `>= 0.50` threshold stayed conservative.
  Reuse: For advisory analyzers, always emit an inspectable artifact and a successful exit path even when the current corpus yields no findings, then let threshold tuning happen explicitly in a later refinement.

## Relevant Runtime Surfaces
- [skills/skill-refiner/SKILL.md](../../../../../skills/skill-refiner/SKILL.md)
- [README.md](../../../../../README.md)
- [skills/run-summarizer/SKILL.md](../../../../../skills/run-summarizer/SKILL.md)
- [skills/docker-smoke-test/SKILL.md](../../../../../skills/docker-smoke-test/SKILL.md)
- [packages/moltfarm/experimental/codex_corpus.py](../../../../../packages/moltfarm/experimental/codex_corpus.py)
- [packages/moltfarm/experimental/codex_timeline.py](../../../../../packages/moltfarm/experimental/codex_timeline.py)
- [tmp/codex-skill-corpus/20260327-185100-520564/report.json](../../../../../tmp/codex-skill-corpus/20260327-185100-520564/report.json)
- [packages/moltfarm/cli.py](../../../../../packages/moltfarm/cli.py)

## Supporting Lesson Files
- [lessons/2026-03-20-run-summarizer-refinement.md](../../../../../lessons/2026-03-20-run-summarizer-refinement.md)
- [lessons/2026-03-21-docker-smoke-test-refinement.md](../../../../../lessons/2026-03-21-docker-smoke-test-refinement.md)
- [lessons/2026-03-28-codex-skill-system-harness.md](../../../../../lessons/2026-03-28-codex-skill-system-harness.md)
- [lessons/2026-03-28-conversational-eval-authoring.md](../../../../../lessons/2026-03-28-conversational-eval-authoring.md)
- [lessons/2026-03-28-molt-cli-evals-refinement.md](../../../../../lessons/2026-03-28-molt-cli-evals-refinement.md)
- [lessons/2026-03-28-skill-near-dupe-scanner.md](../../../../../lessons/2026-03-28-skill-near-dupe-scanner.md)
- [lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md](../../../../../lessons/2026-03-29-pytest-suite-ceiling-after-grader-hardening.md)
- [lessons/2026-04-09-workflow-first-system-map-from-lessons.md](../../../../../lessons/2026-04-09-workflow-first-system-map-from-lessons.md)
