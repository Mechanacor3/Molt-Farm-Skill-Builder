# Pytest Suite Ceiling After Grader Hardening

Source:
- evaluator: `packages/moltfarm/skill_evaluator.py`
- evaluator tests: `tests/test_skill_evaluator.py`
- new skill: `skills/python-pytest-essentials/`
- benchmark: `skills/python-pytest-essentials/evals/workspace/iteration-1/benchmark.json`
- follow-up report: `experiments/python_testing_bakeoff/2026-03-29-python-pytest-essentials-followup.md`

## Grader Hardening Lesson

- `lesson`: Recovering paraphrased grader outputs is necessary, but once that recovery is in place, a generic eval suite may stop separating skill quality from baseline capability.
- `evidence`: After hardening grading alignment and rerunning the six-case pytest suite for `python-pytest-essentials`, both the with-skill and without-skill configurations scored a perfect `1.0` weighted pass rate across all six cases.
- `scope`: skill eval design and interpretation
- `reuse`: When a suite suddenly becomes all ties after a grader fix, treat that as evidence that the suite is saturated, not that every skill is equally good.

## Fair Recomparison Lesson

- `lesson`: Any leaderboard produced before a grader-behavior change should be treated as historical, not directly comparable to post-fix runs.
- `evidence`: The original upstream pytest bake-off highlighted Luxor and Mindrally, but the post-fix `python-pytest-essentials` run used a materially different grading path and therefore cannot be ranked fairly against those earlier numbers without rerunning them.
- `scope`: benchmark comparison discipline
- `reuse`: After changing grader alignment, rerun the top comparison set or explicitly label the new run as a follow-up on a changed eval surface.

## Discriminative Suite Lesson

- `lesson`: To distinguish a specialist pytest skill from a strong foundation model, eval cases must demand more than generic correctness.
- `evidence`: The six-case suite covered practical pytest patterns well, but after grading was hardened the no-skill baseline still satisfied every case.
- `scope`: pytest skill evaluation
- `reuse`: Add cases or checks that reward compactness, sharper tool choice, anti-pattern avoidance, or repo-specific precision if the goal is to separate strong skills from a strong general baseline.
