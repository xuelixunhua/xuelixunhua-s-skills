---
name: llm-wiki-workspace
description: Build and maintain a local markdown-first LLM Wiki for research or project folders. Use this whenever the user wants to turn notes, markdown files, PDFs, spreadsheets, images, scripts, reports, or mixed project folders into a persistent wiki. This skill should trigger both when the user wants the classic `raw/ + wiki/ + scripts/ + outputs/ + tmp/` structure and when they want to semantically compile an already-mature workspace into a maintainable wiki without aggressively moving files. Also use it when the user mentions LLM Wiki, compiled knowledge bases, Obsidian-style research repos, source ingestion, source promotion, wiki linting, semantic indexing of folders, or asks how to make a large local folder understandable and editable by the LLM over time.
---

# LLM Wiki Workspace

This skill turns a local folder into a maintainable LLM Wiki.

The important idea is not "make everything markdown" or "move everything into a new tree."
The important idea is to create a stable knowledge layer that helps the model answer three questions:

- what is this file or folder
- what role does it play in the project
- what durable knowledge should be promoted from it

## Core model

Treat the workspace as cooperating layers rather than one big pile:

1. user-authored working notes or canonical master notes
2. source material and raw assets
3. compiled knowledge maintained by the LLM
4. tooling, outputs, and temporary intermediates

The wiki is not the same thing as the full project directory.
It is the durable knowledge and navigation layer inside the project.

## Two operating modes

This skill now supports two valid ways to build an LLM Wiki.

### Mode 1: Structure-first

Use this mode when the folder is still loose, early, or obviously under-structured.

Typical signs:

- files are scattered and unnamed
- there is no obvious source-of-truth note
- scripts, raw inputs, outputs, and drafts are mixed together
- the user wants a clean baseline layout

In this mode, create or normalize toward a layout like:

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

This mode is best when the physical layout itself needs help.

### Mode 2: Compilation-first

Use this mode when the project already has a meaningful structure and the real problem is that the folder is not yet legible to the LLM.

Typical signs:

- the project already has stable directories with working dependencies
- there is already a knowledge folder, notes folder, scripts folder, or outputs folder
- moving files aggressively would create risk or churn
- the user wants the model to understand the workspace semantically before reorganizing it physically

In this mode, do not start by moving files.
Start by compiling the workspace into a semantic map:

- classify each directory and important file
- explain what each one means
- identify which files are sources, which are compiled knowledge, which are tools, and which are outputs
- create a `wiki/` layer that indexes and interprets the existing structure
- decide later whether any physical reorganization is still worth doing

This mode is best when the project's main deficit is understanding, not storage layout.

## What "compilation" means here

Compilation is the process of turning a filesystem into a maintainable semantic graph.

The goal is to map:

`file or folder -> role -> evidence -> reusable knowledge -> query path`

A good compilation pass should answer:

- what this file is
- why it exists
- what other files depend on it
- whether it is raw material, compiled knowledge, tooling, output, or noise
- whether its contents should be promoted into a durable wiki page

This is why compilation usually comes before reorganization in mature workspaces.
Once the model understands the project, any later moves become smaller and safer.

## Choosing the mode

Decide the mode after inspecting the existing folder.

Use this checklist:

- If the workspace is chaotic and low-structure, choose structure-first.
- If the workspace is functional but hard to interpret, choose compilation-first.
- If the workspace has one strong area and one weak area, use a hybrid approach:
  keep the stable parts in place, and add structure only where needed.

When in doubt, bias toward compilation-first.
It is usually safer to build understanding around an existing project than to immediately rearrange it.

## Schema and local instructions

The schema is usually implemented through `AGENTS.md` or a similar repo-local instruction file.
It tells the LLM:

- which directories are source-of-truth inputs
- which directories may be edited freely
- what page types exist in `wiki/`
- where outputs and intermediates belong
- what to update during bootstrap, compile, ingest, query, promote, and lint

Without this schema, the model behaves like a generic assistant.
With it, the model behaves like a workspace maintainer.

## Page types

Read [references/page-types.md](references/page-types.md) when deciding how to classify new pages.
The default vocabulary is:

- `sources/` for one source at a time
- `topics/` for recurring subject areas
- `entities/` for stable named things
- `synthesis/` for cross-source analysis worth preserving

If the project already has a canonical master note, that note may continue to serve as the main synthesis page.

## Placement rules

Use these rules consistently, but adapt them to the workspace instead of forcing a reset:

- Keep user-authored raw notes in `notes/` unless there is already a canonical master note elsewhere.
- Keep external source files in `raw/` when the project is using structure-first mode.
- In compilation-first mode, existing source directories may remain in place and be mapped through the wiki.
- Keep binary inputs and datasets out of `wiki/`.
- Keep scripts in `scripts/` or existing tool directories.
- Keep reproducible deliverables in `outputs/` or existing output directories.
- Keep scratch files and extracted intermediates in `tmp/`.
- Keep compiled markdown knowledge in `wiki/` and/or the project's existing canonical knowledge folder.

Do not move files aggressively.
Prefer creating a semantic layer around stable project structure unless a move is obviously low-risk.

## File classification rubric

Before writing pages, classify important directories and files into one of these buckets:

1. raw sources
2. compiled knowledge
3. scripts or tools
4. generated outputs
5. temporary intermediates
6. cache, local config, or noise

Do not treat every markdown file as a wiki page.
Many markdown files are source material, working notes, exports, or outputs rather than durable knowledge.

## Main operations

Read [references/workflows.md](references/workflows.md) when choosing how to ingest or lint a workspace.

### Bootstrap

Use bootstrap when the folder already contains useful work but lacks a stable maintenance layer.

Checklist:

1. inspect the existing folder before designing anything
2. identify the canonical notes or master synthesis pages
3. choose structure-first or compilation-first mode
4. create the minimal skeleton needed for that mode
5. write or update `AGENTS.md`
6. create `wiki/index.md`, `wiki/log.md`, and templates

### Compile

Use compile when the user wants the model to understand the workspace itself.

Checklist:

1. inventory major directories and important files
2. classify them by role
3. explain what each directory means in the project
4. identify durable knowledge already present
5. identify source material that still needs promotion
6. build wiki pages that let future queries start from a stable index

Useful outputs from a compile pass often include:

- a workspace map
- a source inventory
- a script or code inventory
- a synthesis page explaining the workspace's knowledge production flow

### Ingest

When a new source arrives:

1. read the source from `raw/`, an existing source directory, or a user-designated note
2. create or update a page in `wiki/sources/`
3. promote durable findings into `wiki/topics/`, `wiki/entities/`, or `wiki/synthesis/`
4. update `wiki/index.md`
5. append a short entry to `wiki/log.md`

### Query

Default query behavior is read-first:

1. read `wiki/index.md`
2. read the minimum relevant pages
3. answer with references to the wiki and, when needed, raw sources
4. only write back into the wiki when the answer is clearly durable or the user wants it preserved

### Promote

Promote a result into the wiki when it becomes reusable knowledge, such as:

- a durable comparison
- a cross-source synthesis
- a clarified concept definition
- a recurring framework or checklist
- a code or workflow explanation that the project will reuse

When new evidence changes an older claim, update the existing page rather than creating a disconnected mini-summary.

### Lint

Periodically check for:

- orphan pages
- stale claims
- duplicate concepts
- missing cross-links
- source summaries that never got promoted
- scripts whose purpose is undocumented
- outputs with no provenance note

## Working with scripts and data

Treat scripts as tools, not as knowledge pages.

- Keep generation and extraction code in `scripts/` or the project's existing tool directories.
- Keep raw spreadsheets, CSVs, exports, images, PDFs, and datasets out of `wiki/`.
- Keep cleaned or generated datasets in `outputs/data/` unless they are temporary, in which case use `tmp/`.
- Document the purpose, inputs, outputs, and important assumptions of major scripts in the wiki.

If a script writes artifacts, prefer routing them to `outputs/` instead of the project root when that change is safe.
In mature projects, it is often enough to document the current output path first and move it later.

## Writing conventions

- Prefer markdown for wiki pages.
- Use human-readable page names.
- Link related pages eagerly.
- Use frontmatter only when it helps indexing or downstream tooling.
- Prefer strengthening existing durable pages over creating parallel summary files.

## Deliverables

When asked to set up or maintain an LLM Wiki workspace, usually produce:

- the repo-local `AGENTS.md` schema
- the directory skeleton, if needed
- `wiki/index.md` and `wiki/log.md`
- templates in `wiki/_templates/`
- source or synthesis pages for important materials
- safe path or output fixes where clearly beneficial

When running in compilation-first mode, also strongly consider producing:

- a workspace compilation map
- a folder and file role inventory
- a code or script inventory
- a summary of what is already compiled knowledge versus what still needs promotion

When useful, add a short `README.md` explaining how the workspace is meant to be maintained over time.
