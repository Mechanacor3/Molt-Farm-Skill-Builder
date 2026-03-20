---
name: repo-triage
description: Quickly assess a repository task and output a terse triage in Goal, State, Next form. Use when a repo, issue, PR, workflow, or local code change needs a fast assessment rather than a full solution.
---

# Repo Triage

Use this skill when:
- A repo task, issue, PR, or workflow needs a fast local assessment.
- The user wants a short, actionable read on what is going on and what to inspect next.
- Inputs are narrow and local to the current repository.

Instructions:
1. Read only the task input and the smallest necessary local repository context.
2. Do not fetch network resources, run builds, or scan the entire repository unless explicitly requested.
3. Stay in triage mode only. Do not propose a full implementation.
4. Produce exactly these sections in this order:
   Goal: one sentence stating the likely objective.
   State: one or two evidence-backed observations. Cite file paths or file paths with lines when relevant.
   Next: one to three concrete next actions. Start each action with a verb.
5. Keep the whole output short. No greetings, no chatty framing, and no meta commentary.
6. If critical information is missing, add a `Missing:` line naming the smallest extra file or path needed.
7. If something is unknown, mark it with `Unknown:` instead of guessing.
8. When helpful, use this checklist to guide inspection without reproducing it in the output: @./references/triage-checklist.md
