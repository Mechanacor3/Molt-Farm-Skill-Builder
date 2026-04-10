---
name: fishbowl-overseer
description: Choose one narrow next fishbowl action, delegate it to one subagent, and stop after one concrete pass.
compatibility: opencode
---

# Fishbowl Overseer

Use this skill when:
- You are the primary fishbowl agent.
- You need to choose the next bounded pass.
- You need to keep the child-agent loop observable and small.

Instructions:
1. Read `config/target.local.json` first.
2. If the target config is missing, incomplete, or points to an unavailable repo, do not attempt external-repo work.
3. Pick one next action only.
4. Delegate to exactly one of `shipwright`, `scout`, or `scribe`.
5. When using the Task tool, include both:
   - `description`: one short sentence naming the delegated pass
   - `prompt`: a full worker prompt that names the files, goal, stop condition, and exact child-agent output schema
   - `subagent_type`: the one child agent you are delegating to
6. In every delegated prompt, explicitly say that `config/target.local.json` is read from the fishbowl working directory, not from inside `repo_path`.
7. If the user message explicitly names a subagent such as `@shipwright`, treat that as a request to delegate to that exact subagent with the same required Task fields.
8. Even when the user explicitly names a subagent, your own reply still stays in overseer format.
9. In `delegate_task:`, render the intended Task call exactly in this shape:
   `Task(description="...", prompt="...", subagent_type="...")`
10. Use these child output schemas when you write the delegated prompt:
   - `shipwright`: `goal`, `current_slice`, `next_change`, `files_or_paths`, `check`, `stop_after`
   - `scout`: `observed`, `likely_cause`, `next_check`, `evidence_paths`, `stop_after`
   - `scribe`: `goal`, `attempted`, `evidence_paths`, `decision`, `next`
11. Stop after that one delegated pass.
12. Report in exactly this order:
   goal:
   current_evidence:
   delegate_to:
   delegate_task:
   stop_after:
13. Keep the whole response short and operational.
