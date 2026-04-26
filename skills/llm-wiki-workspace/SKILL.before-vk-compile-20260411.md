---
name: llm-wiki-workspace
description: Build and maintain a local markdown-first LLM Wiki for research or project folders. Use this whenever the user wants to turn notes, markdown files, PDFs, spreadsheets, images, or scripts into a persistent wiki with `raw/`, `wiki/`, `scripts/`, `outputs/`, `tmp/`, `index.md`, `log.md`, and an `AGENTS.md` schema. Also use it when the user mentions LLM Wiki, compiled knowledge bases, Obsidian-style research repos, source ingestion, source promotion, wiki linting, or asks how to organize mixed note/data/script workspaces so the LLM can maintain them over time.
---

# LLM Wiki Workspace

This skill turns a markdown-heavy local folder into a maintainable LLM Wiki. The goal is not to dump every file into a wiki. The goal is to separate:

- raw facts
- compiled knowledge
- tools that help produce or inspect both

## Core model

Treat the workspace as four cooperating layers:

1. `notes/` or existing master notes: user-authored working notes, drafts, reading notes, meeting notes
2. `raw/`: immutable or mostly immutable source material such as markdown articles, PDFs, spreadsheets, images, exports, datasets
3. `wiki/`: compiled markdown knowledge maintained by the LLM
4. `scripts/`, `outputs/`, `tmp/`: tooling, generated artifacts, and intermediates

The wiki is not the same thing as the full project directory. It is the durable knowledge layer inside the project.

## What Schema Means Here

The schema is usually implemented through `AGENTS.md` or a similar repo-local instruction file. It tells the LLM:

- which directories are source-of-truth inputs
- which directories may be edited freely
- which page types exist in `wiki/`
- what to update during `ingest`, `query`, `promote`, and `lint`
- where generated artifacts and temporary files belong

Without this schema, the model behaves like a generic assistant. With it, the model behaves like a disciplined maintainer of the workspace.

## Directory Baseline

Use this layout unless the user already has a strong existing structure:

```text
project/
  AGENTS.md
  README.md
  notes/
  raw/
    articles/
    data/
    docs/
    images/
  wiki/
    sources/
    topics/
    entities/
    synthesis/
    _templates/
    index.md
    log.md
  scripts/
  outputs/
    figures/
    data/
    reports/
  tmp/
```

Adapt to the project rather than forcing a full reset. If the user already has a long-lived master note, preserve it and wire the rest of the wiki around it.

Read [references/page-types.md](references/page-types.md) when deciding how to classify new pages.
Read [references/workflows.md](references/workflows.md) when choosing how to ingest or lint a workspace.

## Placement Rules

Use these rules consistently:

- Keep user-authored raw notes in `notes/` unless the user already has a canonical master note elsewhere.
- Keep external source files in `raw/`.
- Keep binary inputs and datasets out of `wiki/`.
- Keep scripts in `scripts/`.
- Keep reproducible deliverables in `outputs/`.
- Keep scratch files and extracted intermediates in `tmp/`.
- Keep compiled markdown knowledge in `wiki/`.

Do not move files aggressively. Prefer creating structure around existing important files unless a move is obviously low-risk.

## Main Operations

### Bootstrap

When first setting up a workspace:

1. Inspect the existing folder before designing anything.
2. Identify whether there is already a canonical note or synthesis document.
3. Create the directory skeleton.
4. Write `AGENTS.md` to describe local conventions.
5. Create `wiki/index.md`, `wiki/log.md`, and page templates.
6. Move only the obviously generated files and scripts if the reorganization is safe.

### Ingest

When a new source arrives:

1. Read the source from `raw/` or a user-designated note.
2. Create or update a page in `wiki/sources/`.
3. Promote durable findings into `wiki/topics/`, `wiki/entities/`, or `wiki/synthesis/`.
4. Update `wiki/index.md`.
5. Append a short entry to `wiki/log.md`.

Do not treat every markdown file as an automatic wiki page. Many markdown files are source material or working notes.

### Query

Default query behavior is read-first:

1. Read `wiki/index.md` to find likely pages.
2. Read the relevant pages.
3. Answer with citations to the wiki and, when needed, the raw sources.
4. Only write back into the wiki when the user wants the answer preserved or the result is clearly durable.

### Promote

Promote a query result into the wiki when it becomes reusable knowledge, such as:

- a durable comparison
- a cross-source synthesis
- a clarified concept definition
- a recurring framework or checklist

### Lint

Periodically check for:

- orphan pages
- stale claims
- duplicate concepts
- missing cross-links
- source summaries that never got promoted
- generated outputs with no script or provenance note

## Working With Scripts and Data

Treat scripts as tools, not as knowledge pages.

- Keep generation and extraction code in `scripts/`.
- Keep raw spreadsheets, CSVs, pickle files, and exports in `raw/data/`.
- Keep cleaned or generated datasets in `outputs/data/` unless they are temporary, in which case use `tmp/`.
- Document the purpose and expected output location of important scripts in `README.md` or comments.

If a script writes artifacts, prefer routing them to `outputs/` instead of the project root.

## Writing Conventions

- Prefer markdown for wiki pages.
- Use frontmatter only when it helps indexing or downstream tools.
- Keep page names human-readable.
- Link related pages eagerly.
- When new evidence modifies an older claim, update the old page rather than creating a disconnected mini-summary.

## Deliverables

When asked to set up or maintain an LLM Wiki workspace, usually produce:

- the skill-aware or repo-local `AGENTS.md`
- the directory skeleton
- `wiki/index.md` and `wiki/log.md`
- a few templates in `wiki/_templates/`
- any safe script-path or output-path fixes needed to fit the structure

When useful, also add a short `README.md` that explains how the workspace is meant to be used.
