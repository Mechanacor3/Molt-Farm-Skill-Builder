# Skill Instructions

The portable `SKILL.md` layer where repo-specific guidance should live.

## Working Guidance
### Stable
- Refine a skill by rerunning the same concrete input before and after the edit, then compare output shape and evidence handling. Supporting lesson: [lessons/2026-03-20-run-summarizer-refinement.md](../../lessons/2026-03-20-run-summarizer-refinement.md)
  Evidence: The same target run `runs/run-20260320191724-fff0f529.json` produced a looser first summary and a tighter revised summary after only the skill instructions changed.
  Reuse: When improving a skill, keep the test case fixed, change only the skill, and compare the two outputs before promoting the lesson.
- Repo-specific workflow behavior is easier to evolve when the runtime is backed by a local skill artifact rather than hidden prompt text. Supporting lesson: [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
  Evidence: The new `eval-author` behavior lives in `skills/eval-author/SKILL.md`, while the runtime module focuses on session lifecycle, probe orchestration, and artifact writing.
  Reuse: When a new capability contains reusable review logic or domain guidance, capture that guidance as a portable skill and keep the runtime layer narrow.

### Tentative
- Authoring-loop skills need an explicit "short ordered actions and commands" instruction to keep local-model responses operational instead of essay-like. Supporting lesson: [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
  Evidence: The first local subject output for `molt-skill-builder-authoring` got the sequence right but expanded into headings and narrative in `iteration-1/.../outputs/summary.txt`, which led to a follow-up tightening of the skill instructions.
  Reuse: When evals expect concise workflow guidance, tell the skill to answer as a short ordered sequence of actions and commands.

## Relevant Runtime Surfaces
- [skills/skill-refiner/SKILL.md](../../skills/skill-refiner/SKILL.md)
- [skills/molt-skill-builder-authoring/SKILL.md](../../skills/molt-skill-builder-authoring/SKILL.md)
- [skills/llm-wiki/SKILL.md](../../skills/llm-wiki/SKILL.md)
- [skills/run-summarizer/SKILL.md](../../skills/run-summarizer/SKILL.md)
- [packages/moltfarm/cli.py](../../packages/moltfarm/cli.py)
- [packages/moltfarm/eval_authoring.py](../../packages/moltfarm/eval_authoring.py)
- [skills/eval-author/SKILL.md](../../skills/eval-author/SKILL.md)
- [packages/moltfarm/skill_evaluator.py](../../packages/moltfarm/skill_evaluator.py)

## Supporting Lesson Files
- [lessons/2026-03-20-run-summarizer-refinement.md](../../lessons/2026-03-20-run-summarizer-refinement.md)
- [lessons/2026-03-28-conversational-eval-authoring.md](../../lessons/2026-03-28-conversational-eval-authoring.md)
- [lessons/2026-04-09-skill-authoring-and-wiki-validation.md](../../lessons/2026-04-09-skill-authoring-and-wiki-validation.md)
