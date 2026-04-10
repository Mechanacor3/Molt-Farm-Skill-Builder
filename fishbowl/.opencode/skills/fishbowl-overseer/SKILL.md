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
5. Stop after that one delegated pass.
6. Report in exactly this order:
   goal:
   current_evidence:
   delegate_to:
   delegate_task:
   stop_after:
7. Keep the whole response short and operational.
