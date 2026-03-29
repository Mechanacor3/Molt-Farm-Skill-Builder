# Molt Farm Skill Builder

Molt Farm Skill Builder is for people who write local `SKILL.md` skills and for people who run those skills through a small CLI to evaluate outcomes, inspect artifacts, and refine behavior over time.

## Prerequisites

- Python `>=3.12`
- An editable install of this repo
- OpenAI credentials available in the environment or in `.env`

If you prefer, put `OPENAI_API_KEY=...` in `.env` at the repo root. The CLI loads `.env` automatically.

## Quick Start

Copy-paste this to install the repo locally and run one skill eval end to end:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
export OPENAI_API_KEY=your_key_here
./molt skill-builder eval-skill run-summarizer
```

After it finishes, inspect:

- `skills/run-summarizer/evals/workspace/iteration-N/benchmark.json`
- `skills/run-summarizer/evals/workspace/iteration-N/feedback.json`
- `skills/run-summarizer/evals/workspace/iteration-N/eval-<case-id>/comparison.json`

## Tests

If you want local test tooling in your existing virtualenv, install the repo with the `test` extra:

```bash
pip install -e ".[test]"
python -m pytest tests
```

Run coverage for the Python package:

```bash
python -m pytest tests --cov=moltfarm --cov-report=term-missing
```

Write an HTML coverage report:

```bash
python -m pytest tests --cov=moltfarm --cov-report=html
```

That HTML report is written to `htmlcov/index.html`.

If you do not want to install test dependencies into `.venv`, run the same commands ad hoc with `uv`:

```bash
uv run --with pytest python -m pytest tests
uv run --with pytest --with pytest-cov python -m pytest tests --cov=moltfarm --cov-report=term-missing
```

## For Skill Authors

The normal authoring loop is:

1. Create or edit `skills/<name>/SKILL.md`.
2. Run `./molt skill-builder create-evals <name>` or hand-author `skills/<name>/evals/evals.json`.
3. Run `./molt skill-builder eval-skill <name>`.
4. Inspect `benchmark.json`, `feedback.json`, and per-case `comparison.json`.
5. Refine the skill and rerun the eval.

### Skill Layout

Most authored skills follow this shape:

```text
skills/<name>/
  SKILL.md
  references/
  scripts/
  evals/
    evals.json
    files/
```

### Build Evals

In this repo, “build evals” still means producing `skills/<name>/evals/evals.json`, but you can now either author that file directly or draft it through a resumable conversation.

Draft a new suite or extension:

```bash
./molt skill-builder create-evals run-summarizer
```

That command creates a local draft session under:

- `skills/<skill>/evals/workspace/create-evals/session-N/session.json`
- `skills/<skill>/evals/workspace/create-evals/session-N/analysis/suggested-flavors.json`
- `skills/<skill>/evals/workspace/create-evals/session-N/probes/`

Select flavors and materialize the draft:

```bash
./molt skill-builder create-evals run-summarizer \
  --session session-1 \
  --answer selected_flavors=core-task,evidence-discipline
```

Promote the accepted draft into canonical eval files:

```bash
./molt skill-builder create-evals run-summarizer \
  --session session-1 \
  --promote
```

The promoted suite remains inspectable through the full session workspace, and the command stops before `eval-skill` so you can review the draft first.

Example:

```json
{
  "skill_name": "sample-skill",
  "evals": [
    {
      "id": "case-one",
      "prompt": "Summarize evals/files/sample.json for a human reviewer.",
      "expected_output": "A short summary that states the outcome and cites the artifact.",
      "files": ["evals/files/sample.json"],
      "checks": [
        {
          "text": "The answer makes the task outcome clear",
          "category": "goal",
          "weight": 3
        },
        {
          "text": "The answer cites the attached artifact",
          "category": "evidence",
          "weight": 2
        },
        {
          "text": "The answer keeps the required output shape",
          "category": "format",
          "weight": 1
        }
      ],
      "required_skill_activations": ["sample-skill"]
    }
  ]
}
```

Supported check categories are `goal`, `evidence`, `format`, and `trigger`. Use weighted checks to make task completion and evidence matter more than formatting. When trigger behavior matters, `required_skill_activations` records trace-based trigger checks under the `trigger` category.

### Evaluate a Skill

Run the current skill against its local eval suite:

```bash
./molt skill-builder eval-skill run-summarizer
```

Run with a snapshot baseline:

```bash
./molt skill-builder eval-skill run-summarizer --baseline snapshot --snapshot-current
```

Important artifacts:

- `skills/<skill>/evals/workspace/iteration-N/benchmark.json`
  - aggregate pass rates, category scores, `with_skill_win_rate`, and `task_uplift_score`
- `skills/<skill>/evals/workspace/iteration-N/feedback.json`
  - review notes keyed by eval case
- `skills/<skill>/evals/workspace/iteration-N/eval-<case-id>/comparison.json`
  - winner, confidence, rationale, category deltas, and cost delta for that case
- `skills/<skill>/evals/workspace/create-evals/session-N/`
  - draft sessions, suggested flavors, probe evidence, draft fixtures, and promotion backups

## For CLI Users

Use `./molt skill-builder run <operation>` when you want to run one of the built-in local operations with narrow inputs.

Example:

```bash
./molt skill-builder run manual-lesson-extraction \
  --input source_path=runs/run-20260320192451-9157aace.json \
  --input comparison_path=runs/run-20260320192637-6d787114.json
```

That command reads the two provided run records and writes or updates:

- `runs/<run-id>.json`
- `logs/YYYY-MM-DD/<run-id>.log`

The CLI prints the resulting `run_id`, `run_path`, and `log_path` when it completes.

### Built-in Operations

Current built-in operations:

- `manual-docker-smoke-test`: propose one narrow Docker build-and-run smoke test for a local repo or artifact
- `manual-lesson-extraction`: review a run or log and extract lessons
- `manual-python-build`: build or repair a local Python project with narrow context
- `manual-run-summary`: summarize a completed run record
- `manual-skill-finding`: choose the best existing skill or identify a missing one for a task
- `manual-skill-refinement`: refine an existing skill from a brief plus supporting lessons and eval artifacts
- `manual-triage`: run a narrow repository triage task

After any operation run, inspect:

- `runs/<run-id>.json`
- `logs/YYYY-MM-DD/<run-id>.log`

## Repo Layout

The main directories you will use are:

- `skills/`: reusable skills anchored by `SKILL.md`
- `lessons/`: durable lesson files extracted from runs and evals
- `runs/`: structured run records
- `logs/`: dated log files for completed runs
- `packages/`: the Python runtime and CLI that support the skill loop

## Docker

Docker is optional and secondary to the local workflow above.

```bash
docker build -t moltfarm-skillbuilder .
docker run --rm -it moltfarm-skillbuilder ./molt skill-builder --help
docker run --rm -it moltfarm-skillbuilder ./molt skill-builder eval-skill run-summarizer
```

To keep writes in your working tree, bind-mount the repo:

```bash
docker run --rm -it -v "$PWD:/app" -w /app moltfarm-skillbuilder ./molt skill-builder run manual-lesson-extraction --input source_path=runs/<run-id>.json
```

## Further Reading

- [Skills Guide](./Skills_Guide.md) for deeper guidance on writing stronger skills and eval suites
