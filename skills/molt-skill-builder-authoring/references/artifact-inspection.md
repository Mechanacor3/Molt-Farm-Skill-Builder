# Artifact Inspection Order

Open eval artifacts in this order before changing the skill:

1. `skills/<name>/evals/workspace/iteration-N/benchmark.json`
- Use this for the overall pass rate, uplift, and case distribution.
2. `skills/<name>/evals/workspace/iteration-N/feedback.json`
- Use this for the grader's compact summary of what is wrong or missing.
3. `skills/<name>/evals/workspace/iteration-N/eval-<case-id>/comparison.json`
- Use this to see where `with_skill` won, lost, or tied on one case.
4. `skills/<name>/evals/workspace/iteration-N/eval-<case-id>/with_skill/`
5. `skills/<name>/evals/workspace/iteration-N/eval-<case-id>/without_skill/`
- Compare the paired outputs before editing `SKILL.md` so the change is tied to observed evidence.

Promote a lesson only after the evidence shows a repeatable pattern, not just one vague complaint.
