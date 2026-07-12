# Vertical Knowledge Base Harness

Use this reference when the user wants an LLM Wiki to become a vertical or domain knowledge base.
This is not ordinary folder cleanup and not ordinary RAG setup.
The target is a durable domain judgment system that lets future agents apply a field's knowledge to real situations.

## Core philosophy

A vertical knowledge base should be organized around three material layers:

1. **First layer: bottom materials**
   Raw or bottom-layer material, including original books, reports, PDFs, transcripts, datasets, backtests, outputs, cases, and other source documents. Preserve provenance and avoid over-processing at the folder-maintenance stage. When a first-layer source is useful but not worth a standalone second-layer note or a third-layer rewrite, compress it into a viewpoint index entry instead of leaving only keywords.
2. **Second layer: type-organized compression**
   Material that has already been sorted or compressed by source type, book type, method type, or user workflow. Examples include book notes, method notes, source cards, and self-produced intermediate notes. A report becomes second-layer material only when it deserves a reusable standalone note; many first-layer reports should be indexed directly instead.
3. **Third layer: recomposed domain knowledge**
   The domain body that no longer follows one source's table of contents. It contains definitions, assumptions, concepts, mechanisms, schools, variables, conflicts, judgment routines, and application logic.

The knowledge base also needs an **application entry**: README/AGENTS instructions, indexes, diagnostic questions, and optional playbooks that tell future agents how to call the knowledge when a real situation appears.

The key shift is from "what does this source say?" to "what future problem should this knowledge help interpret?"

## Framework-source double loop

Vertical knowledge bases mature through a double loop, not through a one-time taxonomy.
Use this pattern when the user is still ingesting books, reports, transcripts, cases, or external method references and expects the domain framework to evolve.

The loop is:

```text
provisional framework
  -> incoming source
  -> candidate concepts, mechanisms, cases, scenarios, relations
  -> integration decision
  -> framework or schema adjustment
  -> next source
```

For each new source, make one of six integration decisions:

| Decision | Meaning | Write-back target |
| --- | --- | --- |
| Reinforces | The source supports an existing concept, mechanism, or routine | strengthen the existing third-layer section and source lineage |
| Refines | The source sharpens a boundary, variable, failure mode, or application condition | update the existing concept/routine instead of adding a parallel page |
| Extends | The source introduces a genuinely new concept, mechanism, scenario, case, or relation type | add the smallest necessary node or section, then link it back |
| Contradicts | The source conflicts with the current framework or another source | record the tension, evidence shape, and current judgment |
| Reclassifies | The source shows that the existing framework layer, object type, or relation type is wrong | update the framework/schema and explain the change briefly |
| Parks | The source is interesting but not yet reliable, central, or actionable | keep a compact viewpoint index entry or open question |

Do not treat the current framework as permanent.
Name the current framework/schema implicitly in the durable notes through clear headings, object types, relation types, and source rules.
If a new source changes the framework, update the existing third-layer page rather than creating a disconnected "new version" summary.

Use lightweight schema language:

- **Object types**: what kinds of things the knowledge base tracks, such as concept, mechanism, scenario, source, case, actor, event, tool, metric, or routine.
- **Relation types**: what connections are allowed, such as supports, contradicts, causes, precedes, applies_to, risks, source_of, variant_of, and boundary_of.
- **Instances**: concrete entries of those types, such as `解释权`, `功劳归因`, `功劳被抢`, or a specific source book.

For personal/domain knowledge bases, schema is a thinking aid before it is a database.
Do not force every useful note into frontmatter or JSON unless downstream tooling truly needs it.

## Method-learning mode

Use method-learning mode when the user is studying an external knowledge website, industry map, graph product, or wiki method and wants to learn the approach before building anything.

The output should be a durable method note or an update to an existing method note, not an automatic site scaffold.

The method note should preserve:

1. what the external artifact is trying to do
2. what its domain skeleton is
3. what object types and relation types it appears to use
4. how it likely gathers, compiles, or updates data
5. what can transfer to the user's domain
6. what should not be copied
7. whether implementation is deferred, experimental, or ready to start

If the user explicitly says they are not building the site yet, state that boundary in the note.
Do not create `site/`, graph data, schemas, build scripts, or new content trees from a method-learning request unless the user asks to begin implementation.

## When to choose this branch

Choose vertical knowledge base mode when the user asks to:

- build or extend a vertical knowledge base
- make book notes useful over the long term
- awaken dormant knowledge when a related real event appears
- turn a domain such as power, technical analysis, options, macro finance, organization power, cooking, travel, or AI skills into a reusable knowledge system
- combine several books, reports, transcripts, or long notes into a domain framework
- create a harness, material index, application entry, or domain reasoning system

Do not choose this branch for simple file cleanup, one-off summarization, or a single source note unless the user explicitly wants the result to become part of a lasting domain system.

## Default harness

Adapt names to the workspace language and existing conventions.
For a new vertical knowledge base, prefer a small human-readable harness before adding many control pages:

```text
domain-topic/
  README.md
  AGENTS.md
  【第三层】<Domain>.md
  【索引】<Domain>资料索引.md
  01-第一层-底层资料/
    研报/
    原文/
    应用案例/
    输出/
  02-第二层-类型整理/
    书籍笔记/
    研报笔记/
    方法笔记/
  03-第三层-二次整理/   # optional when there are multiple third-layer notes
  wiki/                 # optional for larger workspaces
    index.md
    log.md
```

If the workspace already has a strong human-facing master note, keep it in place.
The harness should point to it instead of replacing it.

Do not create `source-map.md`, `concept-map.md`, `mechanism-map.md`, `scenario-triggers.md`, or `application-playbook.md` by default.
Those are optional expansions only when the domain is large enough that separate control pages are clearer than one strong main note plus an index.

## File roles

### Third-layer main note

The third-layer main note is the first reading target.
It should contain the domain body:

- definitions and assumptions
- core concepts and confusing distinctions
- mechanisms and causal or operational chains
- schools, frameworks, or competing lenses
- variables, indicators, failure modes, and applicability boundaries
- reusable judgment routines

This note is not a bibliography and not a one-source summary.
Strengthen it before creating parallel third-layer files.

### Material index

The material index is reference infrastructure, not the domain body.
It should separate:

- first-layer bottom materials
- second-layer type-organized notes
- third-layer recomposed notes
- source conflicts or unresolved claims
- where future agents should read next

It may mention first-layer sources, but those index sections must stay separate from the third-layer body.
First-layer sources do not need to pass through the second layer. If a source only needs provenance, topic tags, callable conclusions, and links to the third-layer body, keep it in the material index instead of creating a standalone second-layer note.
Keep extraction status, OCR failures, and processing diagnostics out of the durable material index; report them in chat or temporary audit files instead.

### First-layer viewpoint index entries

Use viewpoint index entries for first-layer material that has been read or reliably extracted, contains useful domain signal, but does not yet deserve a standalone second-layer note or direct third-layer integration.

This pattern applies across source types:

- reports: capture the research conclusion, method, evidence shape, and applicability boundary
- books or chapters: capture the reusable concept, argument, model, or contradiction without reproducing the book structure
- transcripts, courses, interviews, or meetings: capture the operating principle, decision routine, diagnostic question, or lived case logic
- backtests, datasets, outputs, or cases: capture what phenomenon they show, what question they answer, and what their limits are
- images, charts, or tables: capture the finding and interpretation path, not only the visual label

A viewpoint index entry should answer four questions in compressed form:

1. What is the source about?
2. What conclusion, mechanism, or judgment does it contribute?
3. When should a future agent call it?
4. Which third-layer concept, routine, boundary, or open question does it support?

Preferred entry shape:

```markdown
- `<Source name>`: <one compact core conclusion>. <key mechanism, evidence, or boundary>. 支撑 `<third-layer tag>`、`<third-layer tag>`、`<use-case tag>`.
```

For a narrow source, one or two sentences are enough. For a dense method source, three to five compressed sentences are acceptable. If the entry keeps growing, that is evidence the source should become a second-layer note or should update the third-layer main note.

Do not leave a processed source as only filename plus keywords. Keywords help retrieval, but conclusions make the index useful. A durable material index should be a call surface, not a directory listing.

Do not add a confident viewpoint entry for a source that has not actually been read, extracted, OCRed, or otherwise understood. In that case, either keep a minimal provenance listing or report the processing status outside the durable index.

Use the source's role to choose the compression lens:

- **Method or framework source**: extract the reusable model, variables, mechanism chain, evidence shape, and failure boundary. The entry should help future agents know how to reason with the method, not merely where it came from.
- **Single signal, concept, or tool source**: extract what the signal claims to measure, whether the evidence supports the claim, what hidden driver may explain the effect, and when the signal should be redefined, filtered, or ignored.
- **Application, cross-asset, case, or output source**: extract what changes when the same method enters a new asset, scenario, market regime, workflow, or lived case. The entry should preserve the transfer condition and the reason the result may not generalize.

### README

The README is the human-facing entrance.
It should explain:

- what the domain covers
- the recommended read order
- the three material layers
- what is in scope and out of scope
- the next maintenance step

### AGENTS.md

AGENTS.md is the machine-facing local instruction file.
It should tell future agents:

- required read order
- layer definitions
- initial build and supplemental build rules
- where new materials should go
- when to update the third-layer main note
- when to update the index
- what not to move or include

### Optional application pages

Create separate pages only when the material justifies them:

- `【应用】<Domain>调用说明.md` for diagnostic questions and answer routines
- `【案例】<Domain>案例库.md` for applied examples
- `【问题】<Domain>开放问题.md` for gaps and unresolved tensions
- `wiki/domain/...` for a large workspace that truly needs a machine-facing control plane

## Initial build

Use initial build when no durable vertical knowledge base exists yet, or when the existing folder only has sources and notes.

Workflow:

1. Inspect the folder first.
   Identify existing master notes, source folders, book notes, reports, scripts, outputs, and temporary material.
2. Define the domain boundary.
   Name what belongs, what is adjacent, and what is out of scope.
3. Define the application target.
   Write the real problems the knowledge base should help answer, such as decisions, diagnosis, interpretation, strategy, analysis, or writing.
4. Inventory material by layer.
   Separate first-layer bottom materials, second-layer type-organized notes, and third-layer recomposed material.
5. Create or repair the default harness.
   Add the three-layer folders, third-layer main note if one exists or can be safely started, material index, README, and AGENTS.md.
6. Promote existing knowledge cautiously.
   Move or copy ideas into the right layer by strengthening existing durable pages where possible.
7. Update navigation.
   Refresh README, AGENTS.md, material index, and any existing wiki index/log.

Stop when a future agent can answer:

- what the domain is for
- which file to read first
- where lower-level materials live
- how to decide whether a new file is first, second, or third layer
- how to answer a future applied question and when to write back

## Supplemental build

Use supplemental build when the vertical knowledge base already exists and the user wants to add new books, notes, reports, transcripts, cases, or frameworks.

Workflow:

1. Read the existing entry material first.
   Start with README, AGENTS.md, the third-layer main note, and the material index.
2. Classify the incoming material.
   Decide whether it is first-layer source material, second-layer compressed material, a third-layer framework update, a case, a contradiction, or an open question.
3. Run the framework-source double loop.
   Decide whether the new material reinforces, refines, extends, contradicts, reclassifies, or should be parked.
4. Preserve source lineage.
   Update the material index when provenance matters. For many reports, chapters, transcripts, cases, or outputs, viewpoint-index treatment is enough.
5. Strengthen existing pages.
   Merge durable knowledge into the third-layer main note or a relevant existing third-layer page instead of creating a parallel summary.
6. Resolve conflicts explicitly.
   If the new material disagrees with existing claims, mark the tension, evidence, and current judgment.
7. Update navigation.
   Refresh README, AGENTS.md, material index, cross-links, and log if present.
8. Stop when the new material has a clear role.
   It should either update a layer, a concept, a mechanism, a case, source lineage, framework/schema boundary, or an open question.

## Query behavior

When answering a future question against a vertical knowledge base:

1. Read README and AGENTS.md if present.
2. Read the third-layer main note first.
3. Use the material index to find the minimum relevant second-layer or first-layer files.
4. Answer by separating:
   - observed facts from the user's situation
   - domain concepts being invoked
   - mechanism interpretation
   - source evidence and source limits
   - uncertainty and next diagnostic questions or actions
5. If the answer becomes reusable, update the third-layer main note, material index, application page, case page, or open questions.

## Quality bar

A vertical knowledge base is working when:

- it has a clear domain boundary
- the first reading target is obvious
- the three material layers are not mixed together
- source lineage is preserved without turning the workspace into a bibliography
- third-layer knowledge recomposes sources into a better problem structure
- new material is integrated into existing pages instead of accumulating disconnected summaries
- applied cases can improve the framework over time

Avoid:

- making a giant bibliography with no third-layer body
- copying a book's chapter order as the domain structure when a better problem structure exists
- overfitting the knowledge base to one source
- creating many thin files when one stronger main note or index would be clearer
- treating every chat answer as durable without checking whether it changes the framework
