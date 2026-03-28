# Codex Skill System Harness Lessons

Source:
- feature: `packages/moltfarm/experimental/codex_timeline.py`
- corpus runner: `packages/moltfarm/experimental/codex_corpus.py`
- validation method: unit test suite plus real-log corpus run
- corpus report: `tmp/codex-skill-corpus/20260327-185100-520564/report.json`

## Canonicalization Lesson

- `lesson`: Normalize external run logs into one canonical event stream before extracting skill evidence.
- `evidence`: The analyzer only became reliable across both flat Codex `--json` logs and archived `~/.codex/archived_sessions` logs after the normalization layer was added behind `analyze_codex_jsonl`.
- `scope`: skill timeline and trace-ingestion work
- `reuse`: When a feature consumes multiple artifact formats, split the work into `load -> normalize -> extract` so the extraction logic stays format-agnostic.

## Observable Evidence Lesson

- `lesson`: Treat explicit skill-file reads as stronger evidence than agent self-report.
- `evidence`: The Game Lab cases passed because the harness counted `.../skills/.../SKILL.md` path reads directly, while agent claim text remained secondary and non-invoking.
- `scope`: skill-usage measurement
- `reuse`: Count file and resource reads as invocation evidence first, then keep free-text claims as supporting evidence rather than the primary signal.

## Negative Case Lesson

- `lesson`: Every real-log detection harness needs at least one real negative case where the correct answer is zero invocations.
- `evidence`: The archived-session case passed only because the analyzer ignored skill paths embedded in wrapper text and instructions, instead of mistaking them for actual skill use.
- `scope`: parser and eval harness design
- `reuse`: Pair positive cases with at least one real artifact that contains tempting false signals, and lock the expected result to zero.

## Order Preservation Lesson

- `lesson`: Preserve source order exactly when one command references multiple skills.
- `evidence`: The `gamelab-autotrigger` case only became meaningful once the analyzer emitted `develop-web-game` and then `playwright` from a single shell command in left-to-right order.
- `scope`: event timeline generation
- `reuse`: When multiple evidence hits come from one command or record, emit them in source order instead of collapsing or re-sorting them.

## Manifest Lesson

- `lesson`: Put real regression cases behind a tracked manifest instead of relying on ad hoc manual reruns.
- `evidence`: `tests/system/codex_skill_corpus.json` captured the concrete log paths and expected skill orders, which turned the external log corpus into a repeatable pass/fail system check.
- `scope`: local-first system testing
- `reuse`: For parser and trace-analysis work, track a small manifest of real cases with explicit expectations so regressions fail in a repeatable way.
