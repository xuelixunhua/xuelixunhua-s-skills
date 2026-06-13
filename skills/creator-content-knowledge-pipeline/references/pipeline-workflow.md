# Pipeline Workflow

Use this reference when running an actual creator-to-knowledge-base project.

## Phase 0: Scope

Define the project before touching files:

- Creator or source:
- Platform:
- Series or topic:
- Date range:
- Expected item count:
- Output product:
- Public/private boundary:
- Update frequency:

If the user only provides a homepage, first build a source inventory and ask whether all content or a subset should be processed when the scope is ambiguous and expensive.

## Phase 1: Workspace

Recommended conceptual structure:

```text
project/
  README.md
  data/
    source_index.csv
    classification.csv
    public_index.csv
  raw/
    page_exports/
  audio/
  transcripts/
  notes/
  outputs/
  logs/
  tmp/
```

If publishing to GitHub or another public surface, create a separate clean release folder or repo:

```text
public-repo/
  README.md
  data/
    video_index.csv
  notes/
  docs/
```

Do not publish `audio/`, raw transcripts, local absolute paths, platform transId values, browser export logs, or credentials.

## Phase 2: Source Inventory

Minimum fields:

```text
date
platform_id
title
series
subseries
knowledge_theme
duration
play_count
url
status
local_transcript_path
```

For public indexes, remove local paths and internal IDs:

```text
date
platform_id
title
series
subseries
knowledge_theme
duration
play_count
url
```

Completeness checks:

- compare platform count with local count
- list failures explicitly
- identify duplicates, missing titles, missing dates, and private/deleted items
- do not claim complete until every source is either processed or explicitly marked unavailable

## Phase 3: Acquisition

Choose the lightest reliable source path.

Preferred order:

1. Existing local transcript or caption when accurate enough
2. Platform metadata API or command-line extraction
3. Audio-only download for transcription
4. Browser automation for dynamic pages or logged-in workflows

For Bilibili, prefer audio-only when the target is transcription. Keep source URL, BV ID, and sanitized filename together.

For any platform:

- avoid downloading more than needed
- log failed items
- avoid bypassing paywalls, DRM, or access controls
- keep large files in a disposable working layer

## Phase 4: Transcription

Use the user's available transcription path. When using a web transcription tool:

- use `web-access` or the current reliable browser backend if login/upload/download is needed
- batch uploads conservatively
- record transcription status
- verify downloaded transcript count against uploaded audio count
- keep transcripts private by default

Transcript quality checks:

- title matches source
- duration roughly matches source
- text is non-empty and not mostly boilerplate
- speaker labels or punctuation are usable enough for synthesis

## Phase 5: Classification

Classify at multiple levels:

- series or playlist
- subseries or route stage
- knowledge theme
- product value
- public output type

Common knowledge themes:

- geography and landforms
- routes and infrastructure
- history and public memory
- local industry and economy
- border and state space
- food, ritual, and everyday life
- creator worldview or method

Classification is not decoration. It determines what notes should exist.

## Phase 6: Synthesis

Prefer durable structures over episode summaries.

Useful note types:

- master framework
- route or timeline note
- regional/topic note
- concept note
- source card
- public README
- maintenance log

Write for future reuse:

- explain why the place/topic matters
- connect source details into a larger structure
- preserve concrete evidence and examples
- avoid backstage language such as "transcript says", "material shows", "we should next"
- avoid turning notes into generic AI summaries

## Phase 7: Packaging

Choose product shape:

- private local wiki
- public GitHub repository
- Notion/Obsidian workspace
- article series
- course outline
- dataset plus notes

For public GitHub repos:

- include README
- include clean public index
- include notes in stable folders
- include source boundary and non-affiliation statement
- do not include raw audio/video/transcripts unless rights and intent are explicit
- add useful topics through GitHub settings, not as README work notes

## Phase 8: Cleanup

After verifying transcripts and final notes:

- delete disposable audio/video if not needed
- keep transcript and index only if they are useful for future updates
- keep logs if they explain failures
- ensure public repo has no local absolute paths

Report cleaned size when possible.

## Phase 9: Maintenance

Leave an update path:

```text
1. Refresh source inventory.
2. Detect new items.
3. Download/transcribe only new items.
4. Classify new items.
5. Decide whether each item updates existing notes or creates a new note.
6. Rebuild public index.
7. Commit/publish.
8. Clean intermediates.
```

For long-lived projects, prefer strengthening existing master notes over creating parallel summaries.
