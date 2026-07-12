---
name: pdf-to-markdown-pipeline
description: Convert PDFs into reliable, reusable Markdown and structured document artifacts through inspection, extraction, layout-aware structuring, evidence tracking, strict quality gates, review/backfill, and rebuild. Trigger for PDF 转 Markdown, PDF 结构化, OCR 清洗, PDF 公式/表格抽取, MinerU or similar document-conversion workflows. Do not use for a one-page plain-text extraction when no quality or structure work is needed.
---

# PDF to Markdown Pipeline

## Mission

Turn a PDF into a trustworthy Markdown deliverable that can be read, searched,
audited, cited, corrected, and consumed by downstream analysis. The output is
not a blind OCR dump and not a summary: it preserves document structure,
source locations, formulas, tables, appendices, and unresolved quality risks.

## Success Criteria

- The source PDF and processing scope are identified before extraction.
- The final Markdown is readable and structurally useful, with a matching
  structured representation when downstream reuse requires it.
- Formula, table, OCR, layout, and page-artifact risks are surfaced rather than
  silently flattened.
- Every correction can be traced to a source page or review decision.
- Unresolved high-risk items remain explicit and block a formal-delivery claim.
- Downstream analysis consumes only artifacts that passed the relevant gate.

## Skill Type

Hybrid: a fixed document-conversion workflow wrapped in an evidence-first
decision framework.

## Trigger Surface

Use this skill for requests such as:

- “把这个 PDF 转成 Markdown，并保留目录、条款、附录和表格。”
- “PDF 抽取出来有乱码、页脚、公式错乱，帮我清洗并校验。”
- “用 MinerU / OCR / 多模态把 PDF 结构化，但不要直接相信首版结果。”
- “把规则书、教材、政策文件转成可检索、可回填的 Markdown 底座。”
- “比较两版 PDF 前，先把每一版稳定地结构化。”

Absorb nearby cases involving scanned PDFs, long books, appendices, formulas,
tables, page images, review queues, or source-grounded document QA. Do not
trigger for simple copy-paste extraction when the user only needs raw text and
no structure, provenance, or quality decision is required.

## Strategy Philosophy

1. Define the deliverable before choosing the parser. A readable draft,
   reusable Markdown, structured JSON, evidence package, or formal-delivery
   artifact has different quality bars.
2. Inspect the document before committing to an extraction engine. Use the
   cheapest method that preserves the required information, and escalate only
   when page-level evidence shows it is needed.
3. Treat intermediate results as evidence, not truth. Extraction reports,
   layout blocks, OCR output, formula candidates, and model suggestions are
   inputs to review.
4. Separate conversion from interpretation. The general layer produces a
   source-grounded document base; domain analysis belongs downstream.
5. Make uncertainty durable. A review queue is better than a guessed formula,
   fabricated table cell, or falsely clean Markdown file.
6. Correct the structured source and rebuild the final Markdown. Do not create
   a second manually edited document that can drift from JSON or evidence.
7. Stop when the requested gate is met. Do not add expensive OCR, multimodal
   processing, or downstream analysis without evidence that it improves the
   requested deliverable.

## Minimum Complete Toolkit

- A native PDF text/layout extractor such as `pypdf`, `pdfplumber`, or `fitz`.
- An optional layout-aware/OCR engine such as MinerU for scanned or complex
  pages; it is an upstream candidate generator, not a final authority.
- A renderer or page-image viewer for key-page verification.
- A structure builder that emits Markdown and, when useful, structured JSON.
- An evidence manifest or review queue linking pages, blocks, clauses,
  appendices, formulas, tables, and audit issues.
- An audit step that can fail a formal-delivery run.
- A patch/backfill mechanism that updates the structured source and rebuilds
  Markdown, evidence, and downstream artifacts.

## Necessary Facts and Boundaries

- Final reusable artifacts are normally Markdown plus structured JSON. Evidence
  is the quality-control and correction layer, not the default downstream text.
- A parser's “formula review recommended” or “OCR page detected” signal must
  become an explicit review state; it must not be silently ignored.
- Native text extraction is the default for text-heavy PDFs. Layout-aware or
  OCR extraction is selected by page evidence, not by tool popularity.
- OCR is useful for locating text and recovering page content. It is not by
  itself a reliable source for LaTeX formulas or complex tables.
- Multimodal extraction may propose a formula or table, but the result remains
  a candidate until it passes source-page review and the delivery audit.
- Never guess an unreadable formula, variable subscript, table value, or
  diagram relationship just to empty the review queue.
- Keep review notes, patch rationale, and raw diagnostics in the evidence
  layer; do not pollute final document prose with internal commentary.
- On Windows, resolve and print input paths first. If an external engine is
  fragile with Chinese paths, stage a copy under a safe ASCII runtime name and
  preserve the mapping in the manifest.

## Workflow and Decision Points

### 1. Scope and inventory

Identify the exact PDF files, versions, page counts, duplicates, split scope,
and expected output. For a compiled volume, decide whether it should be split
into logical modules before structuring. Preserve the original file and record
its hash or another stable identity.

### 2. Inspect before extracting

Run a lightweight inspection for page count, text-layer availability, page
quality, likely scanned pages, headers/footers, formulas, tables, and appendices.
Choose the first engine from the evidence:

- text layer is good → native extraction with layout-aware fallback;
- text exists but order is broken → layout/block extraction;
- pages are scanned or text quality is poor → OCR/layout-aware extraction;
- formulas or dense tables are damaged → page-image review and targeted
  multimodal/manual transcription.

### 3. Extract a raw, traceable intermediate

Write page-aware raw text and a page-quality report to a temporary or staging
area. Keep page boundaries and extraction metadata. Never treat the raw text as
the final Markdown; it is the input for structure detection and risk scoring.

### 4. Build the structural layer

Convert the intermediate into a document model such as:

`document → sections/clauses → appendices → pages/blocks`

Retain titles, numbering, page ranges, content source, quality flags, and
formula/table sensitivity. Generate the first Markdown and, when downstream
queries or comparisons need stable objects, a matching JSON representation.

### 5. Build Evidence and a review queue

Record enough provenance to locate and repair a problem without rescanning the
whole document. A lightweight evidence model usually includes:

`document, page, block, clause, appendix, formula_candidate,
table_candidate, audit_issue, review_queue, backfill_patch`

Each candidate should carry the source page or block, extraction source, a
short preview or hash, confidence/status, and the next review action.

### 6. Audit before downstream use

Run a normal audit for page-number/footer residue, suspicious Unicode, OCR
artifacts, flattened formulas, unclosed LaTeX delimiters, collapsed tables or
flowcharts, overlong blocks, and inconsistent structure. Then run a strict
delivery audit that also checks unresolved review flags and stale raw content in
the structured representation.

Use two modes explicitly:

- draft mode: findings may remain, but the artifact must say what is unresolved;
- delivery mode: blocking findings fail the run and prevent formal downstream
  analysis or publication.

### 7. Review, backfill, and rebuild

For each review item, inspect the source page and surrounding context. Reuse a
verified cache first; otherwise use the appropriate automated, multimodal, or
human path. Write a patch against the structured object, including the corrected
content source and review status. Rebuild Markdown and JSON, regenerate
Evidence, and rerun the audit.

The loop is:

`audit → review queue → source-page check → patch → rebuild → evidence → audit`

### 8. Release only the appropriate layer

Only after the conversion gate passes should the workflow generate parameter
catalogs, version diffs, spreadsheets, business analysis, front-end data, or
document QA answers. If the gate does not pass, label downstream results as
drafts and carry the unresolved risks forward.

## Output Guidance

For a normal reusable conversion, produce:

1. final Markdown;
2. structured JSON when stable object-level reuse is needed;
3. a source manifest with input identity and output paths;
4. a concise audit report;
5. a review queue or an explicit “no blocking findings” result.

For a one-off draft, the first four may be compressed, but unresolved formulas,
tables, OCR pages, and provenance gaps must still be stated. Do not present a
plain text dump as a high-confidence structured conversion.

## Examples

- “把这本扫描版规则书转成 Markdown，目录、附录和公式都要尽量保留。”
- “这批 PDF 首轮抽取有页脚和公式乱码，建立复核队列并修正。”
- “两版政策 PDF 要做差异分析，先建立带页码证据的结构化底座。”

## Resource Map

- Open `references/pdf-to-markdown-method.md` for the generalized method,
  object model, quality gates, and engine-escalation matrix.
- Use the local project's own parser, renderer, builder, audit, and backfill
  scripts when they exist; this skill defines their order and boundaries rather
  than replacing project-specific implementations.
- If the user asks for domain interpretation after conversion, keep the
  conversion gate visible and route the interpretation to the relevant domain
  workflow instead of expanding this skill with business-specific rules.
