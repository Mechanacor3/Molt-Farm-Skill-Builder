# Python Testing Skill Bake-Off Lessons

Source:
- source storage: `example_upstream_skills/python_testing_bakeoff/`
- local eval copies: `skills/upstream-python-testing-bakeoff/`
- near-dupe report: `tmp/python_testing_bakeoff/near-dupe-report.json`
- benchmark summary: `tmp/python_testing_bakeoff/scoreboard.json`
- detailed report: `tmp/python_testing_bakeoff/report.md`

## Near-Dupe Recall Lesson

- `lesson`: The current near-dupe scanner is strong at catching obvious same-name or highly overlapping skills, but it does not yet surface every intuitive family member in a broad skill set.
- `evidence`: In this four-skill pytest bake-off, the scanner surfaced only two candidate pairs and missed every Luxor pairing even though Luxor is clearly part of the same functional family.
- `scope`: upstream skill clustering and sameness detection
- `reuse`: Treat the scanner as an early warning signal, not as a complete clustering pass, especially when long reference-heavy skills may dilute overlap terms.

## Bake-Off Reproducibility Lesson

- `lesson`: Imported upstream skills should be kept twice: once as untouched storage, once as uniquely named local eval copies.
- `evidence`: The untouched source copies preserved exact upstream content for inspection, while the renamed local copies allowed `molt skill-builder eval-skill` to run all four skills without name collisions.
- `scope`: external skill bake-offs
- `reuse`: For future comparisons, stage untouched upstream folders under `example_upstream_skills/` and create minimal local eval copies under `skills/` that only change metadata needed for discovery.

## Grading Reliability Lesson

- `lesson`: Before trusting close bake-off margins, audit grading fallback rates caused by exact-text alignment between requested checks and grader output.
- `evidence`: This bake-off produced many fallback failures, including `12/18` with-skill checks for `wshobson-python-testing-patterns`, which makes small score differences too noisy to overinterpret.
- `scope`: skill evaluation and leaderboard confidence
- `reuse`: Always pair benchmark deltas with a fallback-check audit, and prioritize evaluator hardening before using narrow score gaps to choose a winner.

## Pytest Baseline Lesson

- `lesson`: A concise, focused pytest skill can compete well against broader encyclopedic skills when the suite asks for practical answer patterns rather than exhaustive documentation.
- `evidence`: `mindrally-python-testing` slightly outperformed the no-skill baseline and stayed close to Luxor despite being much shorter than Luxor, ECC, or Wshobson.
- `scope`: skill authoring strategy
- `reuse`: The next locally-authored pytest skill should bias toward compact, high-signal guidance and concrete activation cues rather than maximal breadth.
