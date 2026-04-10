# Authoring Loop

Use this order unless the request clearly needs a different slice:

1. Author or tighten `skills/<name>/SKILL.md`.
2. Add only the minimal supporting files:
- `references/` for details the skill may need later
- `scripts/` only when repeated code or deterministic behavior is needed
- `evals/files/` for inspectable fixtures
- `agents/openai.yaml` for skill-list metadata
3. Draft or extend evals:
- `./molt skill-builder create-evals <name>`
- Inspect `skills/<name>/evals/workspace/create-evals/session-N/`
4. If flavors still need to be selected, resume with:
- `./molt skill-builder create-evals <name> --session session-N --answer selected_flavors=...`
5. Promote the accepted draft:
- `./molt skill-builder create-evals <name> --session session-N --promote`
6. Evaluate the canonical suite:
- `./molt skill-builder eval-skill <name>`
7. Inspect the generated evidence before editing:
- `benchmark.json`
- `feedback.json`
- one or two failing `comparison.json` files
- the paired `with_skill/` and `without_skill/` outputs
8. Record the strongest lesson, refine narrowly, and rerun the eval.

If the user only needs one exact command or one artifact path, use `molt-cli` instead of the broader authoring loop.
