# Workflow Notes

## Bootstrap

Use bootstrap when the folder already contains useful work but lacks a stable maintenance structure.

Checklist:

- identify canonical notes
- identify raw sources
- identify scripts
- identify generated outputs
- create `AGENTS.md`
- create `wiki/index.md` and `wiki/log.md`

## Build Vertical Knowledge Base

Use this when the user wants the workspace to become a domain knowledge base rather than only a clean folder.
Read `references/vertical-knowledge-base.md` for the full harness.

Initial build checklist:

- inspect the folder and identify existing master notes, source folders, and applied cases
- define the domain boundary and application target
- create or repair the three-layer folder structure
- create or update the third-layer main note, material index, README, and AGENTS.md
- create optional application/case/open-question pages only when the material justifies separate files
- update `wiki/index.md` and `wiki/log.md` if the workspace already uses a wiki layer

Supplemental build checklist:

- read README, AGENTS.md, the third-layer main note, and the material index first
- classify incoming material as first-layer source, second-layer compressed note, third-layer framework update, case, conflict, or open question
- index first-layer sources directly when standalone second-layer notes would add clutter
- merge durable knowledge into the existing third-layer body or index
- preserve source lineage and update navigation

## Ingest

Use ingest when new source material arrives.

Checklist:

- read the source
- summarize it in `wiki/sources/`
- update relevant topic or synthesis pages
- add or refresh links in `wiki/index.md`
- append a log entry

## Query

Use query when the user asks a question against the maintained wiki.

Checklist:

- search `wiki/index.md`
- read the minimum set of relevant wiki pages
- answer with references
- decide whether the result should be promoted

## Promote

Use promote when a chat result deserves to become durable knowledge.

Checklist:

- choose the right destination page
- integrate into existing structure
- avoid parallel duplicate pages
- update index and log

## Lint

Use lint to keep the wiki healthy.

Checklist:

- missing links
- stale claims
- duplicate pages
- weak or absent source lineage
- pages that should be merged into a master synthesis
