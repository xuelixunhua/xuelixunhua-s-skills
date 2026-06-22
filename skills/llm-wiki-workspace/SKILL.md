---
name: llm-wiki-workspace
description: Build and maintain markdown-first LLM Wiki workspaces for research or project folders, including vertical/domain knowledge bases. Use when the user wants folder cleanup plus wiki, semantic compilation of a mature workspace without aggressive moves, raw/wiki/scripts/outputs/tmp or shallow input-output structure, source ingestion and promotion, material indexes, filename type tags, Obsidian-style repos, or a folder that stays understandable to LLMs and humans. Also use for long-term application of field notes, dormant knowledge awakening, three-layer source/note/framework organization, vertical knowledge base initial or supplemental builds, domain judgment systems, application playbooks, or field-specific reasoning across books, reports, PDFs, transcripts, datasets, outputs, cases, and mixed folders.
---

# LLM Wiki Workspace

This skill turns a local folder into a maintainable LLM Wiki.

The important idea is not "make everything markdown" or "move everything into a new tree."
The important idea is to create a stable knowledge layer that helps the model answer three questions:

- what is this file or folder
- what role does it play in the project
- what durable knowledge should be promoted from it
- what real-world situations should trigger this knowledge for use

## Core model

Treat the workspace as cooperating layers rather than one big pile:

1. user-authored working notes or canonical master notes
2. source material and raw assets
3. compiled knowledge maintained by the LLM
4. tooling, outputs, and temporary intermediates

The wiki is not the same thing as the full project directory.
It is the durable knowledge and navigation layer inside the project.

When the workspace is meant to become a vertical knowledge base, the target is higher than folder legibility.
The goal is to compile sources, notes, cases, and frameworks into a domain-specific judgment system that can be called when a real situation appears.

## Human-readable input-to-output architecture

An LLM Wiki should serve three readers at once:

- the AI, which needs stable roles, provenance, and promotion paths
- computer search, which benefits from type tags and consistent keywords in filenames
- the human, who needs shallow paths and files that are understandable at a glance

Do not optimize only for the model by burying everything under deep folders.
When a workspace is small or medium-sized, prefer a shallow input-to-output structure:

```text
project/
  README.md
  AGENTS.md
  【总纲】Master note.md
  【方法论】Method note.md
  【笔记】Study note.md
  【素材】Example bank.md
  输入/
    【原文】Source transcript.txt
    【PDF】Report.pdf
  输出/
    【文章】Published draft.md
  wiki/
    sources/
    topics/
    synthesis/
    index.md
    log.md
  tmp/
```

Use the flow:

`输入/ raw source -> wiki/sources/ source note -> root master notes or synthesis -> 输出/ deliverables`

The root may contain the most important human-facing files when that improves daily use.
Use filename type tags such as `【总纲】`, `【方法论】`, `【笔记】`, `【素材】`, `【原文】`, `【来源笔记】`, and `【输出】` when they make the folder easier to scan and search.
Keep conventional machine entrypoints such as `README.md`, `AGENTS.md`, and existing tool config filenames unchanged when changing them would harm automation.

For personal knowledge folders, treat readable processed notes as a human-facing output, not merely as hidden wiki internals.
If a one-source note is polished enough that the user might review, quote, or build from it, place it at the shallow reading layer such as root `【笔记】Topic.md` or `笔记/`.
Use `wiki/sources/` for provenance cards, semantic inventory, large source libraries, or notes that mainly serve AI retrieval.
Do not turn `wiki/sources/` into a place where useful finished notes disappear from the user's normal reading path.

## Three operating branches

This skill supports three valid branches. Choose after inspecting the folder and the user's stated goal.

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
For small personal knowledge folders, a shallower tagged layout may be better than this full skeleton.
Prefer `输入/ + 输出/ + wiki/ + tmp/` plus tagged root notes when that gives a clearer human browsing experience.

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
If the existing folder already uses filename tags like `【笔记】` or has high-frequency notes in the root, preserve that convention unless it is clearly harmful.

### Mode 3: Vertical knowledge base

Use this mode when the user wants a field-specific knowledge system, not just a cleaner folder or a semantic inventory.

Typical signs:

- the user mentions a vertical/domain knowledge base, field knowledge, professional application, or long-term use of notes
- the folder contains books, reports, transcripts, course notes, research notes, or mature master notes around one domain
- the user wants dormant knowledge to be awakened when a related event, case, decision, market move, or relationship problem appears
- the user asks for initial construction or supplemental construction of a domain knowledge base
- the value lies in reusable interpretation, material layering, diagnostic questions, and application entry points rather than one-source summaries

In this mode, read [references/vertical-knowledge-base.md](references/vertical-knowledge-base.md).
Treat the workspace as three material layers plus a clear application entry:

1. first layer: raw or bottom-layer materials, including originals, reports, datasets, backtests, outputs, cases, and source documents
2. second layer: type-organized compression, including book notes, method notes, source cards, and user-organized intermediate notes; report notes belong here only when the report deserves a reusable standalone note
3. third layer: recomposed domain knowledge, including the main body, cross-source frameworks, mechanisms, concepts, and judgment routines
4. application entry: README/AGENTS instructions, indexes, diagnostic questions, and optional playbooks that tell future agents how to call the knowledge base

Support two submodes:

- initial build: create the three-layer folder structure, third-layer main note or index, material index, README/AGENTS instructions, and log or navigation updates
- supplemental build: read the existing third-layer main note and material index first, classify new material into the right layer, update source lineage, and avoid parallel summaries; first-layer sources may be indexed directly with callable conclusions instead of creating second-layer notes

This branch is best when the project's main deficit is not organization but reusable domain judgment.

## What "compilation" means here

Compilation is the process of turning a filesystem into a maintainable semantic graph.

The goal is to map:

`file or folder -> role -> evidence -> reusable knowledge -> reading path + query path`

A good compilation pass should answer:

- what this file is
- why it exists
- what other files depend on it
- whether it is raw material, compiled knowledge, tooling, output, or noise
- whether its contents should be promoted into a durable wiki page
- whether a processed note belongs in the human reading layer instead of only in `wiki/`

This is why compilation usually comes before reorganization in mature workspaces.
Once the model understands the project, any later moves become smaller and safer.

## Choosing the mode

Decide the mode after inspecting the existing folder.

Use this checklist:

- If the workspace is chaotic and low-structure, choose structure-first.
- If the workspace is functional but hard to interpret, choose compilation-first.
- If the user wants a vertical/domain knowledge base or asks how to apply a field's notes over time, choose vertical knowledge base mode.
- If the workspace has one strong area and one weak area, use a hybrid approach:
  keep the stable parts in place, and add structure only where needed.

When in doubt between structure-first and compilation-first, bias toward compilation-first.
When in doubt between compilation-first and vertical knowledge base mode, ask what the durable output should do: make the folder legible, or help answer domain problems in future situations.

## Schema and local instructions

The schema is usually implemented through `AGENTS.md` or a similar repo-local instruction file.
It tells the LLM:

- which directories are source-of-truth inputs
- which directories may be edited freely
- what page types exist in `wiki/`
- where outputs and intermediates belong
- what to update during bootstrap, compile, ingest, query, promote, and lint
- for vertical knowledge bases, what third-layer main note, material index, and application instructions future agents should read first

Without this schema, the model behaves like a generic assistant.
With it, the model behaves like a workspace maintainer.

## Page types

Read [references/page-types.md](references/page-types.md) when deciding how to classify new pages.
The default vocabulary is:

- `sources/` for one source at a time when the page mainly serves provenance or AI retrieval; if it is a finished human-readable note, prefer a shallow tagged note such as `【笔记】...`
- `topics/` for recurring subject areas
- `entities/` for stable named things
- `synthesis/` for cross-source analysis worth preserving
- `domain/` only when a vertical knowledge base truly needs extra machine-facing control pages; by default prefer a third-layer main note, material index, README, and AGENTS instructions

If the project already has a canonical master note, that note may continue to serve as the main synthesis page.

## Placement rules

Use these rules consistently, but adapt them to the workspace instead of forcing a reset:

- Keep user-authored raw notes in `notes/` unless there is already a canonical master note elsewhere.
- Keep external source files in `raw/` or `输入/` when the project is using structure-first mode; prefer the user's existing language and convention.
- In compilation-first mode, existing source directories may remain in place and be mapped through the wiki.
- For human-facing knowledge folders, use filename type tags when they reduce ambiguity and improve search. Avoid renaming automation-sensitive files such as `README.md`, `AGENTS.md`, package manifests, or tool configs unless explicitly requested.
- Avoid deep nesting for frequently opened notes. A shallow root with tagged master notes is often better than forcing every note under `notes/topics/subtopics/...`.
- Keep readable processed notes close to the human reading path. If the user likely will not open `wiki/` during normal review, do not put the only full version of an important note there.
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

Read [references/workflows.md](references/workflows.md) when choosing how to ingest, lint, or extend a workspace.
Read [references/vertical-knowledge-base.md](references/vertical-knowledge-base.md) when the task is to build or supplement a domain knowledge base.

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

### Build or supplement a vertical knowledge base

Use this operation when the user wants the wiki to become a domain judgment system.

Checklist:

1. determine whether this is an initial build or a supplemental build
2. inspect the folder and existing README, AGENTS, third-layer main note, material index, `wiki/index.md`, and log if present
3. define the domain boundary and the real problems the knowledge base should help answer
4. create or update the harness: three-layer folders, third-layer main note, material index, local instructions, and optional application/case/open-question pages only when justified
5. promote source material into the right material layer while preserving provenance
6. update `AGENTS.md`, README, indexes, and logs; when first-layer material is useful but not worth promotion, write a compact viewpoint index entry with keywords, conclusions, boundaries, and third-layer tags
7. stop when a future query has a clear reading path and application routine

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

When running in vertical knowledge base mode, also strongly consider producing:

- a third-layer main note that future agents read before lower-level material
- a material index separating first-layer bottom materials, second-layer type-organized notes, and third-layer recomposed knowledge
- README and AGENTS instructions that define the reading order, boundary, and application routine
- optional application, case, or open-question pages when the domain has enough reusable examples to justify separate files

When useful, add a short `README.md` explaining how the workspace is meant to be maintained over time.
