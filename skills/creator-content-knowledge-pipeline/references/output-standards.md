# Output Standards

Use this reference when deciding what artifacts to create and how polished they must be.

## Artifact Types

### Source inventory

Purpose: prove what was included.

Quality bar:

- source IDs and URLs are accurate
- dates and titles are preserved
- series/category fields are filled
- unavailable items are marked
- public version removes local paths and internal IDs

### Classification overview

Purpose: show the structure of the creator or domain.

Quality bar:

- identifies major series or topic clusters
- explains why each cluster matters
- recommends which clusters deserve deep notes
- avoids just listing counts

### Master framework

Purpose: explain the whole body of content.

Quality bar:

- names the central logic
- shows how categories relate
- identifies the creator/domain's method or worldview
- can absorb future content

### Route, topic, or regional notes

Purpose: turn content into reusable knowledge.

Quality bar:

- not episode-by-episode unless necessary
- clear hierarchy
- concrete facts and examples preserved
- public-facing language
- no backstage production phrases

### Public README

Purpose: explain why the project exists and how to use it.

Quality bar:

- identifies the creator/source
- explains the interpretation
- maps current contents
- states maintenance path
- states source/copyright boundary
- avoids internal work notes or "recommended tags" after publication

### Maintenance log

Purpose: make updates cheap.

Quality bar:

- records date, added items, failures, deleted intermediates, and next update step

## Public/Private Boundary

Default private:

- raw audio
- raw video
- downloaded full transcripts
- upload/download logs
- local absolute paths
- platform job IDs or transIds
- credentials, cookies, session data

Default public:

- cleaned notes
- public-safe source index
- README
- classification overview
- maintenance method

Ask before publishing raw transcripts or large copied text, especially when copyright is unclear.

## Language Quality

Write as knowledge notes, not as work logs.

Avoid:

- "the transcript says"
- "the material mentions"
- "we should do next"
- "this video is about"
- "可沉淀内容"
- "后台"

Prefer:

- direct explanation
- route, region, topic, role, mechanism
- concrete examples
- public-readable framing

## Completion Report

At the end of a run, include:

```text
Source count:
Processed count:
Failed or skipped:
Main artifacts:
Public/private boundary:
Cleaned files:
Update path:
```
