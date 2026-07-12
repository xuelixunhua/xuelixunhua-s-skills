# Bundled PDF Processing Scripts

This directory contains the executable Python layer extracted from the source
project's `0_脚本/通用能力/pdf处理/` toolkit. The scripts are kept together
because several of them import neighboring modules such as
`formula_multimodal.py`, `pdf_toolkit.py`, and `build_rule_structure.py`.

## Main entry point

For a complete conversion gate, start with:

```powershell
python scripts/run_rule_structure_pipeline.py --help
```

The wrapper coordinates:

```text
extract → structure → Evidence/review queue → strict audit
```

For a first-pass inspection or a small one-off extraction, use:

```powershell
python scripts/pdf_toolkit.py inspect --input path/to/source.pdf
python scripts/pdf_toolkit.py extract --input path/to/source.pdf `
  --output-text tmp/pdfs/document_raw.txt `
  --output-json tmp/pdfs/document_report.json
```

Then use the structure, Evidence, audit, and backfill scripts in the order
described in the parent Skill and `references/pdf-to-markdown-method.md`.

## Script groups

### Required conversion path

- `pdf_toolkit.py`
- `build_rule_structure.py`
- `document_evidence.py`
- `audit_markdown_formula.py`
- `apply_structure_backfill.py`
- `run_rule_structure_pipeline.py`

### Optional extraction and review paths

- `run_mineru_local.py`
- `mineru_adapter.py`
- `evaluate_mineru_output.py`
- `build_agent_vision_packets.py`
- `formula_multimodal.py`

### Optional downstream outputs

- `build_parameter_catalog.py`
- `build_clause_diff.py`
- `build_diff_workbook.py`

These derive comparison artifacts from already structured documents; they do
not replace the conversion quality gate.

## Dependencies and boundaries

- Python 3.10+ is recommended.
- `pypdf` is required for native PDF reading and splitting.
- `PyMuPDF` (`fitz`) is required for page rendering and visual review.
- `Pillow` is optional for image normalization in page-review paths.
- `openpyxl` is needed only for `build_diff_workbook.py`.
- MinerU is an optional external CLI used by the MinerU scripts.
- `formula_multimodal.py` uses an OpenAI-compatible HTTP endpoint only when
  model-assisted formula review is explicitly enabled; no API key or secret is
  stored in this Skill.

## Runtime conventions

- Run scripts from the repository root or pass explicit absolute paths.
- Keep raw text, reports, rendered pages, caches, and review queues in a
  project-specific working directory rather than inside the Skill folder.
- On Windows, print resolved input paths and stage an ASCII runtime copy when a
  third-party engine cannot handle Chinese paths.
- Do not treat MinerU or multimodal output as final without the audit and
  source-page review steps.
