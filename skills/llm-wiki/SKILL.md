---
name: llm-wiki
description: Turn raw notes plus reference material into an evidence-backed interlinked Markdown wiki. Use when the target already has or needs a small canonical folder taxonomy and the job is to place supported facts into timeline and entity pages without inventing unsupported details.
---

# LLM Wiki

Use this skill when:
- Raw notes, session logs, source text, or errata need to become curated Markdown wiki pages.
- The target repo or vault may already have canonical folders, index pages, or entity notes that should be preserved.
- The job is to route supported facts into timeline or history pages plus canonical people, places, items, or faction pages.

Instructions:
1. Inspect the target wiki's local rules first: AGENTS or docs, folder taxonomy, naming conventions, link style, and existing index pages.
2. Preserve existing structure when it exists. Update canonical pages instead of inventing parallel folders or duplicate entity files.
3. Separate raw capture from curated output. Timeline or history pages explain sequence; entity pages collect stable facts with links back to supporting notes.
4. Extract only supported facts from the provided notes, reference text, and errata. If sources conflict or a detail is thin, mark it as conflicting, unverified, or TODO instead of resolving it by guesswork.
5. When several sources mention the same entity, route the new fact to the canonical page and add or improve links from timeline or chapter notes rather than repeating the full description everywhere.
6. Match the repo's existing link style. Reuse the canonical page path for repeat mentions whenever possible.
7. Prefer inspectable Markdown outputs: concise overviews, vital stats or timeline fields, major events, references, and index tables when the repo already uses them.
8. If no taxonomy exists, propose the smallest useful default: one history or timeline page, one top-level index, and canonical entity pages only for repeated people, places, or items.
9. Keep edits local-first and narrow. Do not pull in broad unseen corpus context or rewrite unrelated pages.
10. When the user asks what to update, answer with the smallest page-level plan: destination pages, supported facts to add, links to add or repair, and any unresolved conflicts.
11. In that plan, name the exact supporting note, reference excerpt, or errata source path for each non-obvious fact so the edit stays evidence-backed.
12. If the task is review-only and the user wants a critique of a proposed wiki update plan, use `llm-wiki-validator` rather than this authoring skill.
13. When helpful, use `@./references/wiki-workflow.md` for the workflow and `@./references/source-reconciliation.md` for evidence and errata handling.
