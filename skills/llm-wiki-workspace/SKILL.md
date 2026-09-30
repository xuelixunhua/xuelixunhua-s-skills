---
name: llm-wiki-workspace
description: "Organize or maintain a research workspace or domain knowledge base, including source provenance, indexes, and knowledge promotion. Use for durable workspace structure and maintenance."
---

# LLM Wiki Workspace

Maintain a durable, navigable research workspace without losing sources or the user's existing knowledge structure. This skill owns placement, provenance, indexes, and knowledge promotion. `content-master` owns the substantive synthesis when a task also needs new judgments, mechanisms, or prose structure.

## Choose the lightest useful structure

- **Structure first**: for a disorganized folder, identify source files, canonical notes, code, deliverables, and scratch work; organize only as much as navigation requires.
- **Compilation first**: when files already have useful homes, build semantic links and strengthen existing notes without aggressive moves.
- **Vertical knowledge base**: for sustained domain learning, connect first-layer sources, second-layer source notes, and third-layer cross-source frameworks. Initial builds establish the route; supplemental work strengthens it.
- **Method learning**: when the user wants an author's reasoning method, retain the analytical moves and transfer boundary instead of treating the material as a factual source for the domain.

Inspect README, applicable instructions, and the relevant canonical note or index. Do not demand the entire workspace as pre-reading for a local edit. Respect the user's manuscript, existing deletions, and confirmed folder route.

## Invariants

- Give each durable concept one main home. Integrate into existing master/topic notes before creating parallel summaries; do not use source order as the third-layer outline when the domain has a better mechanism structure.
- Preserve source lineage and meaningful disagreements. A citation supports an actual claim; source existence alone is not evidence of full ingestion.
- Keep original sources, generated knowledge, deliverables, and scratch work distinguishable. Do not move, rename, overwrite, or remove sources without checking affected links and recoverability within the authorized scope.
- Human-facing, frequently read notes may stay shallow with descriptive filenames. `wiki/sources/` is useful for provenance and large inventories, not a compulsory home for readable notes. Do not build empty scaffolding or duplicate a project's existing source index.
- An existing `raw/wiki/scripts/outputs/tmp` layout is a convention, not a reason to remodel every folder. Keep private/raw data out of published knowledge and code repositories.

## Maintain both content and structure

For new material, verify its source, identify what changes an existing claim, method, case, conflict, or open question, then update the appropriate note and provenance route. Create a standalone source note only when its detail has continuing value. Update the index when navigation changes and the existing concise log when durable knowledge changes.

Use a double loop: first integrate what fits the current framework; then test whether the new evidence reveals a missing distinction, wrong hierarchy, repeated concept, or changed boundary. Revise the framework when necessary rather than appending more source-by-source sections.

For a query, locate the minimum relevant pages, answer with evidence, and return to raw sources for disputed or missing details. Promote the result only when durable knowledge maintenance is part of the task. Ordinary Q&A does not require writing files.

When linting or restructuring, check broken links, orphaned notes, stale claims, duplication, and weak source lineage. Fix the affected route and preserve a recoverable mapping for moves. Avoid a second catalog that will drift from the existing one.

## Resources and completion

- Workflow selection and maintenance operations: [references/workflows.md](references/workflows.md).
- Page contracts and templates: [references/page-types.md](references/page-types.md), only for pages being created or changed.
- Domain framework compilation: [references/vertical-knowledge-base.md](references/vertical-knowledge-base.md).
- Maintainer evaluation cases: [evals/evals.json](evals/evals.json).

Finish when the requested knowledge is integrated, its source can be traced, relevant links resolve, and the human entry remains usable. Report what changed and any unresolved source boundary; a folder tree or list of summaries alone does not establish a completed knowledge base.
