# PDF to Markdown: Generalized Method

This reference distills a working PDF-structuring practice into a project-
agnostic method. It is intentionally narrower than a PDF library manual: the
important asset is the decision logic and correction boundary.

## 1. The core model

```text
PDF source
  → inspect / split / inventory
  → page-aware extraction
  → structural Markdown + structured JSON
  → Evidence + audit issues + review queue
  → source-page review and patch backfill
  → rebuild Markdown / JSON / Evidence
  → strict delivery gate
  → downstream analysis, diff, QA, or publication
```

The key design choice is to keep three concerns separate:

| Layer | Responsibility | Default consumer |
| --- | --- | --- |
| Conversion | Preserve document structure and readable content | humans and document tools |
| Evidence | Locate, classify, audit, and correct uncertainty | the conversion workflow |
| Interpretation | Explain meaning, compare versions, or make decisions | domain workflows |

Evidence is not a more “complete” Markdown file. It is the control surface that
prevents a bad extraction from quietly becoming a trusted source.

## 2. Why direct PDF-to-Markdown fails

The first extraction often looks acceptable while hiding defects:

- page headers, footers, page numbers, and file codes are mixed into prose;
- columns and reading order are flattened incorrectly;
- formulas lose superscripts, subscripts, operators, or delimiters;
- tables become a single paragraph or an apparently valid but shifted table;
- scanned pages produce partial text with no obvious error marker;
- OCR and model output may invent a plausible character or number;
- a manually edited Markdown copy drifts from the structured source;
- downstream diff or analysis propagates the defect before anyone sees it.

The solution is not “choose the perfect parser.” It is to make detection,
traceability, review, and reconstruction part of the pipeline.

## 3. Engine selection matrix

| Page evidence | First choice | Escalate when | Do not claim |
| --- | --- | --- | --- |
| Clean text layer, simple layout | native text extraction | reading order or symbols are damaged | that raw text preserves layout automatically |
| Text layer exists, multi-column or dense layout | layout/block extraction | blocks still merge or reorder | that line order equals document order |
| Scanned or sparse text layer | OCR/layout-aware engine | OCR confidence or page structure is poor | that OCR output is formula-accurate |
| Formulas, dense tables, diagrams | page image + targeted visual review | source image remains ambiguous | that a plausible transcription is confirmed |
| Large batch with repeated layout | cached/automated specialized engine | recurring error class exceeds audit tolerance | that a specialized engine removes the need for audits |

Use the least expensive engine that meets the required quality. Escalation is
page- or object-specific whenever possible; do not rerun an entire corpus with
an expensive engine because a small set of formula pages needs visual review.

## 4. Intermediate artifacts and object model

Keep these artifacts distinct, even if one script emits several of them:

1. `raw text`: page-aware first-pass extraction;
2. `page report`: text quality, likely OCR/formula/table risk, and recommended
   next action;
3. `structured JSON`: stable document, section, clause, appendix, and content
   fields;
4. `Markdown`: human-readable rendering of the structured document;
5. `Evidence`: source locations, blocks, candidates, audit issues, review state,
   and patch history;
6. `review queue`: actionable items that are not yet safe to treat as final.

A minimal evidence object can be modeled as:

```text
document
  ├─ pages
  │   └─ blocks(page, bbox, kind, text preview/hash)
  ├─ sections / clauses(page range, content, sensitivity, review status)
  ├─ appendices(type, page range, content source)
  ├─ formula candidates(page, source, LaTeX, status, issue)
  ├─ table candidates(page, structure, status, issue)
  ├─ audit issues(severity, location, rule, evidence)
  └─ backfill patches(target, fields, rationale, reviewer)
```

Do not over-model the first version. Add an object when it makes a recurring
error locatable, auditable, or repairable.

## 5. Quality gates

### Normal readability audit

Check for:

- page residue and repeated headers/footers;
- suspicious or private-use Unicode characters;
- broken reading order and repeated/missing blocks;
- formulas rendered as token soup or ordinary prose;
- unbalanced Markdown/LaTeX delimiters;
- tables, lists, and diagrams flattened beyond recognition;
- implausibly long paragraphs or empty sections.

### Strict delivery audit

In addition, check that:

- formula-sensitive objects are not still raw, unreviewed text;
- formula/table candidates have an explicit status;
- structured JSON and Markdown contain the same corrected content;
- old raw content has not reintroduced a repaired defect;
- review notes are not mixed into the final document body;
- blocking issues are zero or explicitly accepted under a named draft status.

“No visible乱码” is not equivalent to “safe for formal delivery.” A document
can be readable while still containing an unresolved formula or table whose
meaning matters downstream.

## 6. Correction contract

When a defect is found, prefer a patch that records:

- target type and stable target ID;
- corrected field(s);
- content source, such as native extraction, OCR, visual review, or manual
  source-page transcription;
- review status and remaining issues;
- source page(s) and a short rationale.

Then:

1. apply the patch to the structured source;
2. regenerate Markdown and any derived JSON fields;
3. rebuild Evidence and the review queue;
4. rerun normal and strict audits;
5. regenerate downstream derived outputs if they already exist.

Never fix only the rendered Markdown when a structured source exists. Never put
internal review reasoning into the final document body unless the user asked for
an annotated research artifact.

## 7. Formula and table policy

Use a separate path for semantically fragile objects:

1. detect candidate pages/blocks during inspection;
2. isolate the object and render the source page at readable resolution;
3. reuse verified cache if available;
4. try targeted multimodal or specialized recognition;
5. compare the proposed result with the source image and surrounding text;
6. accept only when variables, operators, units, bounds, and table structure are
   supported;
7. otherwise keep the item in the review queue.

For diagrams, choose a faithful Markdown table, Mermaid diagram, structured
list, or source image reference according to what preserves meaning. Do not
force every visual into plain text.

## 8. Draft versus delivery mode

Draft mode is useful when the user wants a first pass or wants to inspect the
review queue before investing in corrections. It may contain findings, but the
output must identify them and should not be passed off as final.

Delivery mode is a gate: unresolved blocking issues prevent formal analysis,
publication, or claims of complete conversion. Non-blocking evidence may remain
for traceability if the acceptance rule says so.

## 9. Operational conventions

- Print resolved input paths before batch processing.
- Keep temporary raw text, screenshots, and engine caches outside the final
  Markdown directory.
- Preserve the source-to-output manifest and stable document IDs.
- For Windows paths with Chinese characters, stage safe runtime copies for
  fragile external tools and retain the original path in metadata.
- Use a single source of truth for final content; derived files are rebuilt.
- If a parser or model fails, preserve the failure as an evidence item and move
  to the next valid review path instead of silently skipping the page.

## 10. Stop and escalation rules

Escalate to a heavier parser, OCR engine, or multimodal review when:

- scanned-page ratio is high;
- layout loss affects meaning;
- formulas or table cells are the main output value;
- the same audit finding recurs across many documents;
- downstream consumers need cell-level or formula-level citations.

Keep the light pipeline when the document is text-heavy, the audit is clean, and
the requested result is a readable, source-grounded Markdown document. The goal
is not maximal processing; it is the smallest trustworthy path to the requested
quality bar.
