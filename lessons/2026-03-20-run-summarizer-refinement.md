# Run Summarizer Refinement Lessons

Source:
- skill: `skills/run-summarizer/SKILL.md`
- initial summary run: `runs/run-20260320192451-9157aace.json`
- revised summary run: `runs/run-20260320192637-6d787114.json`
- lesson extraction run: `runs/run-20260320192925-e19d42f7.json`

## Meta Lesson

- `lesson`: Refine a skill by rerunning the same concrete input before and after the edit, then compare output shape and evidence handling.
- `evidence`: The same target run `runs/run-20260320191724-fff0f529.json` produced a looser first summary and a tighter revised summary after only the skill instructions changed.
- `scope`: skill improvement workflow
- `reuse`: When improving a skill, keep the test case fixed, change only the skill, and compare the two outputs before promoting the lesson.

## Output Contract Lessons

- `lesson`: Always include a dedicated gaps field that lists unperformed verifications and unconfirmed assumptions.
- `evidence`: The revised summary adds `gaps: No live build or import/CLI verification; existence of packages/moltfarm/cli.py was not confirmed.` while the initial summary had no explicit gaps field.
- `scope`: run summarization skills
- `reuse`: Require a `gaps` field in summary-style skills whenever the run may leave important checks unperformed.

- `lesson`: Keep the field set fixed and ordered so outputs are easy to scan and compare across runs.
- `evidence`: The revised summary uses `attempted`, `happened`, `status`, `produced`, `gaps`, `next_step` and drops the extra header and top metadata block.
- `scope`: structured reporting skills
- `reuse`: Prefer one stable output contract per skill instead of optional headers or ad hoc metadata sections.

- `lesson`: Treat recorded run status as transport truth, not a synonym for success.
- `evidence`: The first summary rewrote `completed` as `success (completed)`. The revised summary preserves `status: completed` and leaves outcome detail to the other fields.
- `scope`: run summarization skills
- `reuse`: Preserve the run's recorded status verbatim unless the system has a separate evaluated outcome field.

- `lesson`: Make `next_step` one concrete, low-effort verification action instead of a branching plan.
- `evidence`: The revised summary narrows the follow-up to `pip install -e .` and `molt --help`, while the initial summary mixed layout decisions with installation and verification.
- `scope`: action-oriented summary skills
- `reuse`: Prefer one immediate smoke test or validation step that the user can run without additional planning.

- `lesson`: Include artifact paths and run ids where they materially improve traceability.
- `evidence`: The revised summary names the target run id in `happened` and points to the source run record and log in `produced`.
- `scope`: run and log summarization skills
- `reuse`: When summarizing a prior run, cite the source run id and the main artifact paths if they fit cleanly in the output contract.

- `lesson`: State explicitly when no build, install, or file mutation happened.
- `evidence`: The revised summary says `no files changed and no distributions built`, which is more informative than only saying no code changed.
- `scope`: repo and build reporting skills
- `reuse`: In `produced`, name the absence of expected side effects when that absence changes how the output should be interpreted.
