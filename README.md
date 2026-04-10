# Molt Farm Skill Builder

Molt Farm Skill Builder is for people who write local `SKILL.md` skills and for people who run those skills through a small CLI to evaluate outcomes, inspect artifacts, and refine behavior over time.

## Prerequisites

- Python `>=3.12`
- An editable install of this repo
- OpenAI credentials available in the environment or in `.env` for cloud-backed runs, grading, and `create-evals`

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

## Pure Local Pilot

This repo can now run a narrow local-only subject loop against Gemma 4 in two ways:

- direct chat-completions against `llama.cpp`
- experimental proxy-backed Responses through `Molt-Farm-Proxy/README.md`

The first milestone is subject-only. Full local `eval-skill` grading is intentionally out of scope for this pilot.

1. Copy the sample env file:

```bash
cp .env.example .env
```

2. Download a Gemma 4 E4B 4-bit GGUF and normalize the local filename:

```bash
mkdir -p models
ln -sf /absolute/path/to/your-gemma-4-e4b-4bit.gguf models/gemma-4-e4b-q4.gguf
```

The compose file expects `models/gemma-4-e4b-q4.gguf` by default. Override that with `MOLT_GEMMA4_MODEL_FILE` if needed.

3. Start the local Gemma server:

```bash
docker compose --profile local-llm up -d llm-gemma4
```

4. Verify direct local chat-completions:

```bash
curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer local-dev-key" \
  -d '{
    "model": "gemma-4-e4b",
    "messages": [
      {"role": "user", "content": "Say hello from local Gemma 4."}
    ]
  }'
```

### Direct Chat Baseline

Use the direct `llama.cpp` surface as the default local subject path:

```bash
MOLT_SUBJECT_PROVIDER=openai_compatible
MOLT_SUBJECT_MODEL=gemma-4-e4b
MOLT_SUBJECT_BASE_URL=http://127.0.0.1:8080/v1
MOLT_SUBJECT_API_KEY=local-dev-key
```

### Proxy Responses Experiment

Start the proxy in a second terminal, pointed at the same local Gemma server:

```bash
cd Molt-Farm-Proxy
env \
  MOLT_UPSTREAM_BASE_URL=http://127.0.0.1:8080 \
  MOLT_UPSTREAM_API_KEY=local-dev-key \
  uv run molt-proxy-dev --host 127.0.0.1 --port 8000 --upstream-model gemma-4-e4b
```

Then switch the subject provider to the proxy-backed Responses surface:

```bash
MOLT_SUBJECT_PROVIDER=openai_responses
MOLT_SUBJECT_MODEL=gemma-4-e4b
MOLT_SUBJECT_BASE_URL=http://127.0.0.1:8000/v1
MOLT_SUBJECT_API_KEY=local-dev-key
```

You can verify the proxy health and probe path with:

```bash
curl http://127.0.0.1:8000/health
curl -i http://127.0.0.1:8000/v1/responses
```

`GET /v1/responses` should return `405 Method Not Allowed`; that is the expected proxy preflight response.

### Pilot Sequence

Run the same three narrow workflows on either subject path:

```bash
./molt skill-builder run manual-triage --input target=.
./molt skill-builder run manual-run-summary --input run_record_path=runs/<previous-run-id>.json
./molt skill-builder run manual-docker-smoke-test --input dockerfile_path=Dockerfile
```

Inspect these artifacts after each run:

- `runs/<id>.json`
- `jq -r '.output.trace.items[]?.summary' runs/<id>.json`
- `Molt-Farm-Proxy/.molt-logs/proxy-requests.jsonl` for the Responses experiment

The key trace signals are:

- `function_call:activate_skill:*`
- `function_call:read_skill_resource:*`

### Eval-Skill Note

`eval-skill` still supports hybrid local-subject/cloud-grader runs. The local-only pilot in this section does not attempt to make grading fully local yet.

Example hybrid eval:

```bash
OPENAI_API_KEY=your_openai_key_here \
./molt skill-builder eval-skill run-summarizer --model gemma-4-e4b --grader-model gpt-5
```

## Fishbowl Experiment

The `fishbowl/` subtree is a separate local opencode surface for watching small local-model agents work against an external browser-game repo. It owns opencode config, agent prompts, journal files, and lesson capture, but it does not own the 1602-style game source.

Start from the fishbowl root:

```bash
cp fishbowl/config/target.example.json fishbowl/config/target.local.json
cd fishbowl
opencode
```

Point `config/target.local.json` at the external game repo you want the baby molts to work on. The default fishbowl config stays local-only, uses the direct `llama.cpp` baseline at `http://127.0.0.1:8080/v1`, and leaves external-directory access on approval.

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

## System Map

Build a reviewable workflow-first wiki draft from the current lesson corpus:

```bash
./molt skill-builder run manual-system-map-draft
```

Useful filters:

```bash
./molt skill-builder run manual-system-map-draft \
  --input lesson_glob='lessons/*.md' \
  --input workflow_focus=author-skill,build-evals \
  --input date_from=2026-04-01
```

That draft writes a reviewable workspace under:

- `wiki/drafts/session-N/plan.md`
- `wiki/drafts/session-N/pages/`
- `wiki/drafts/session-N/_build/lesson-index.json`

Promote a reviewed draft into canonical wiki pages and the promoted lesson index:

```bash
./molt skill-builder promote-system-map --session session-N
```

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
- `manual-system-map-draft`: synthesize selected lesson files into a reviewable workflow-first wiki draft under `wiki/drafts/session-N/`
- `manual-triage`: run a narrow repository triage task

After any operation run, inspect:

- `runs/<run-id>.json`
- `logs/YYYY-MM-DD/<run-id>.log`

## Repo Layout

The main directories you will use are:

- `skills/`: reusable skills anchored by `SKILL.md`
- `lessons/`: durable lesson files extracted from runs and evals
- `wiki/`: curated workflow-first system map pages plus the promoted lesson index
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

Validate the local llama.cpp compose file without starting it:

```bash
docker compose --profile local-llm config
```

## Further Reading

- [Skills Guide](./Skills_Guide.md) for deeper guidance on writing stronger skills and eval suites
