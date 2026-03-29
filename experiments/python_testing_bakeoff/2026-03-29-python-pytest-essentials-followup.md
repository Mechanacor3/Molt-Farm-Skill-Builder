# Python Pytest Essentials Follow-Up

Date: 2026-03-29

## What Changed

- Hardened grading alignment in `packages/moltfarm/skill_evaluator.py`
  - added explicit prompt guidance to copy check text exactly
  - kept exact-text alignment as the preferred path
  - added conservative recovery for paraphrased grader outputs
- Added a new compact skill:
  - `skills/python-pytest-essentials/`
- Evaluated that skill with the exact same six-case pytest suite used in the upstream bake-off:

```bash
./molt skill-builder eval-skill python-pytest-essentials --snapshot-current --model gpt-5
```

## Result

Benchmark:
- `skills/python-pytest-essentials/evals/workspace/iteration-1/benchmark.json`

Outcome:
- `with_skill` weighted mean: `1.0`
- `without_skill` weighted mean: `1.0`
- weighted delta: `0.0`
- with-skill win rate: `0.0`
- tie rate: `1.0`
- promotion signal: unsuccessful

Interpretation:
- The new skill answered the suite perfectly.
- The no-skill baseline also answered the suite perfectly.
- After grader hardening, this exact suite no longer distinguishes the new skill from a strong general baseline.

## Important Comparison Caveat

The original upstream bake-off scores were produced before the grading-alignment hardening.

That means:
- old upstream scores and this new score are not apples-to-apples
- the new result is still useful because it shows the current suite has hit a ceiling against the baseline

## Practical Conclusion

The compact synthesis was reasonable:
- it preserved Luxor-style async and coverage guidance
- it kept Mindrally-style compactness

But the exact suite is now too easy to prove that advantage after the grader fix.

## Recommended Next Step

To prove a new pytest skill is actually better-than-rest, do one of these next:
- rerun Luxor and Mindrally with the hardened grader for an updated apples-to-apples leaderboard
- strengthen the eval suite with more discriminative checks, especially ones that punish generic-but-correct answers
