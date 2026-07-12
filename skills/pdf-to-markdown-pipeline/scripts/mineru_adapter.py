#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convert MinerU output into inputs used by the shared PDF structure pipeline.

Outputs:
1. raw text with PAGE markers, compatible with build_rule_structure.py
2. page quality report, compatible with document_evidence.py
3. MinerU evidence seed with block/formula/table/image candidates
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pdf_toolkit


FORMULA_BLOCK_RE = re.compile(r"\$\$(.*?)\$\$", re.S)
IMAGE_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
HIGH_RISK_LATEX_RE = re.compile(r"(\\#|\\sharp|\\breve|\\ddot|\\not\s|☉|♯|#)")
MEDIUM_RISK_LATEX_RE = re.compile(r"(\\mathbb)")
SUSPICIOUS_LATEX_RE = re.compile(
    rf"(?:{HIGH_RISK_LATEX_RE.pattern})|(?:{MEDIUM_RISK_LATEX_RE.pattern})"
)
SKIP_RAW_TEXT_TYPES = {"page_number", "footer", "header"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_path(raw_path: str | None, required: bool = False) -> Path | None:
    if not raw_path:
        if required:
            raise SystemExit("Required path argument is empty.")
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if required and not path.exists():
        raise SystemExit(f"Path does not exist: {path}")
    return path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def find_one(directory: Path, suffix: str) -> Path | None:
    matches = sorted(directory.glob(f"*{suffix}"))
    return matches[0] if matches else None


def total_pdf_pages(pdf_path: Path | None) -> int | None:
    if not pdf_path:
        return None
    try:
        PdfReader, _PdfWriter = pdf_toolkit.require_pypdf()
        return len(PdfReader(str(pdf_path)).pages)
    except Exception:
        return None


def preview(text: str, limit: int = 240) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "..."


def text_of(item: dict[str, Any]) -> str:
    return str(
        item.get("text")
        or item.get("latex")
        or item.get("html")
        or item.get("table_body")
        or ""
    )


def item_sort_key(item: dict[str, Any]) -> tuple[int, float, float]:
    page_idx = item.get("page_idx")
    bbox = item.get("bbox")
    page = int(page_idx) if isinstance(page_idx, int) else 0
    if isinstance(bbox, list) and len(bbox) >= 2:
        return page, float(bbox[1]), float(bbox[0])
    return page, 0.0, 0.0


def local_page_indexes(items: Iterable[dict[str, Any]]) -> list[int]:
    pages = sorted({int(item["page_idx"]) for item in items if isinstance(item.get("page_idx"), int)})
    return pages


def physical_page(local_page_idx: int | None, first_page_number: int) -> int | None:
    if local_page_idx is None:
        return None
    return local_page_idx + first_page_number


def raw_text_for_item(item: dict[str, Any]) -> str:
    item_type = str(item.get("type") or "unknown")
    text = text_of(item).strip()
    if not text:
        return ""
    if item_type == "equation":
        if "$$" in text:
            return text
        return f"$$\n{text}\n$$"
    if item_type == "table":
        return text
    if item_type == "image":
        return ""
    return text


def strip_formula_delimiters(text: str) -> str:
    cleaned = str(text or "").strip()
    if cleaned.startswith("$$") and cleaned.endswith("$$") and len(cleaned) >= 4:
        cleaned = cleaned[2:-2].strip()
    return cleaned


def build_raw_text(items: list[dict[str, Any]], first_page_number: int) -> str:
    page_items: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        local_page = item.get("page_idx")
        if not isinstance(local_page, int):
            continue
        if str(item.get("type") or "unknown") in SKIP_RAW_TEXT_TYPES:
            continue
        page_items[local_page].append(item)

    chunks: list[str] = []
    for local_page in sorted(page_items):
        page_number = physical_page(local_page, first_page_number)
        chunks.append("=" * 60)
        chunks.append(f"PAGE {page_number}")
        chunks.append("=" * 60)
        for item in sorted(page_items[local_page], key=item_sort_key):
            text = raw_text_for_item(item)
            if text:
                chunks.append(text.rstrip())
        chunks.append("")
    return "\n".join(chunks).rstrip() + "\n"


def quality_for_page(
    page_number: int,
    text: str,
    page_items: list[dict[str, Any]],
) -> dict[str, Any]:
    score = pdf_toolkit.score_page_text(text)
    type_counter = Counter(str(item.get("type") or "unknown") for item in page_items)
    equation_items = [item for item in page_items if item.get("type") == "equation"]
    table_items = [item for item in page_items if item.get("type") == "table"]
    image_items = [item for item in page_items if item.get("type") == "image"]
    suspicious_equations = [item for item in equation_items if SUSPICIOUS_LATEX_RE.search(text_of(item))]

    flags = list(score.get("flags") or [])
    if equation_items:
        flags.append("mineru_equation_blocks")
    if suspicious_equations:
        flags.append("mineru_suspicious_latex")
    if table_items:
        flags.append("mineru_table_blocks")
    if image_items:
        flags.append("mineru_image_blocks")

    formula_like = bool(score.get("formula_like") or equation_items or suspicious_equations)
    likely_needs_ocr = bool(score.get("likely_needs_ocr"))
    if likely_needs_ocr and formula_like:
        suggested_action = "ocr_and_formula_review"
    elif likely_needs_ocr:
        suggested_action = "ocr_review"
    elif formula_like:
        suggested_action = "formula_review"
    else:
        suggested_action = "native_text_ok"

    return {
        "page": page_number,
        "extraction_engine": "mineru_pipeline",
        "layout_cleanup_applied": False,
        **score,
        "formula_like": formula_like,
        "suggested_action": suggested_action,
        "flags": sorted(set(flags)),
        "mineru_type_counts": dict(sorted(type_counter.items())),
        "mineru_equation_count": len(equation_items),
        "mineru_suspicious_equation_count": len(suspicious_equations),
        "mineru_table_count": len(table_items),
        "mineru_image_count": len(image_items),
    }


def summarize_strategy(page_reports: list[dict[str, Any]]) -> dict[str, Any]:
    strategy = pdf_toolkit.summarize_document_strategy(page_reports)
    strategy["extraction_engine"] = "mineru_pipeline"
    strategy["recommended_pipeline"] = "mineru_first_with_evidence_and_backfill"
    return strategy


def build_report(
    items: list[dict[str, Any]],
    source_pdf: Path | None,
    first_page_number: int,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    page_items: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        local_page = item.get("page_idx")
        if isinstance(local_page, int):
            page_items[local_page].append(item)

    page_reports: list[dict[str, Any]] = []
    for local_page in sorted(page_items):
        text_parts = [
            raw_text_for_item(item)
            for item in sorted(page_items[local_page], key=item_sort_key)
            if str(item.get("type") or "unknown") not in SKIP_RAW_TEXT_TYPES
        ]
        page_number = physical_page(local_page, first_page_number)
        if page_number is None:
            continue
        page_reports.append(quality_for_page(page_number, "\n".join(text_parts), page_items[local_page]))

    pages = [item["page"] for item in page_reports]
    return {
        "schema_version": "mineru_pipeline_report.v1",
        "created_at": now_iso(),
        "input_path": str(source_pdf) if source_pdf else None,
        "page_range": [min(pages), max(pages)] if pages else [None, None],
        "total_pages_in_document": total_pdf_pages(source_pdf) or (max(pages) if pages else 0),
        "pages_requiring_ocr_review": [
            item["page"] for item in page_reports if item.get("likely_needs_ocr")
        ],
        "formula_like_pages": [
            item["page"] for item in page_reports if item.get("formula_like")
        ],
        "pages_requiring_formula_review": [
            item["page"]
            for item in page_reports
            if item.get("suggested_action") in ("formula_review", "ocr_and_formula_review")
        ],
        "document_strategy": summarize_strategy(page_reports),
        "page_reports": page_reports,
        "mineru_artifacts": artifacts,
    }


def artifact_paths(auto_dir: Path) -> dict[str, Any]:
    content_list_path = find_one(auto_dir, "_content_list.json")
    content_list_v2_path = find_one(auto_dir, "_content_list_v2.json")
    markdown_path = find_one(auto_dir, ".md")
    middle_path = find_one(auto_dir, "_middle.json")
    model_path = find_one(auto_dir, "_model.json")
    layout_pdf = find_one(auto_dir, "_layout.pdf")
    span_pdf = find_one(auto_dir, "_span.pdf")
    image_dir = auto_dir / "images"
    return {
        "auto_dir": str(auto_dir),
        "content_list": str(content_list_path) if content_list_path else None,
        "content_list_v2": str(content_list_v2_path) if content_list_v2_path else None,
        "markdown": str(markdown_path) if markdown_path else None,
        "middle_json": str(middle_path) if middle_path else None,
        "model_json": str(model_path) if model_path else None,
        "layout_pdf": str(layout_pdf) if layout_pdf else None,
        "span_pdf": str(span_pdf) if span_pdf else None,
        "image_dir": str(image_dir) if image_dir.exists() else None,
    }


def build_seed(
    items: list[dict[str, Any]],
    auto_dir: Path,
    source_pdf: Path | None,
    first_page_number: int,
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    image_dir = auto_dir / "images"
    image_files = sorted(image_dir.glob("*")) if image_dir.exists() else []
    markdown_path = Path(artifacts["markdown"]) if artifacts.get("markdown") else None
    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path and markdown_path.exists() else ""
    type_counts = Counter(str(item.get("type") or "unknown") for item in items)
    pages = local_page_indexes(items)

    blocks: list[dict[str, Any]] = []
    formula_candidates: list[dict[str, Any]] = []
    table_candidates: list[dict[str, Any]] = []
    image_candidates: list[dict[str, Any]] = []
    for index, item in enumerate(sorted(items, key=item_sort_key), start=1):
        item_type = str(item.get("type") or "unknown")
        local_page = item.get("page_idx") if isinstance(item.get("page_idx"), int) else None
        page_number = physical_page(local_page, first_page_number)
        text = text_of(item)
        block = {
            "id": f"mineru-block-{index:05d}",
            "source": "mineru_content_list",
            "type": item_type,
            "page_idx": local_page,
            "page_number": page_number,
            "bbox": item.get("bbox"),
            "text": text,
            "text_preview": preview(text),
            "raw": item,
        }
        blocks.append(block)
        if item_type == "equation":
            latex = strip_formula_delimiters(text)
            suspicious = bool(SUSPICIOUS_LATEX_RE.search(latex))
            formula_candidates.append(
                {
                    "id": f"mineru-formula-{len(formula_candidates) + 1:05d}",
                    "block_id": block["id"],
                    "page_numbers": [page_number] if page_number else [],
                    "bbox": item.get("bbox"),
                    "latex": latex,
                    "raw_latex": text,
                    "img_path": item.get("img_path"),
                    "status": "candidate" if suspicious else "accepted",
                    "source": "mineru_equation",
                    "review_required": suspicious,
                    "issues": ["mineru_suspicious_latex_tokens"] if suspicious else [],
                }
            )
        elif item_type == "table":
            table_candidates.append(
                {
                    "id": f"mineru-table-{len(table_candidates) + 1:05d}",
                    "block_id": block["id"],
                    "page_numbers": [page_number] if page_number else [],
                    "bbox": item.get("bbox"),
                    "html": text,
                    "img_path": item.get("img_path"),
                    "status": "candidate",
                    "source": "mineru_table",
                    "review_required": True,
                    "issues": ["mineru_table_structure_needs_review"],
                }
            )
        elif item_type == "image":
            image_candidates.append(
                {
                    "id": f"mineru-image-{len(image_candidates) + 1:05d}",
                    "block_id": block["id"],
                    "page_numbers": [page_number] if page_number else [],
                    "bbox": item.get("bbox"),
                    "img_path": item.get("img_path"),
                    "status": "candidate",
                    "source": "mineru_image",
                    "review_required": True,
                    "issues": ["mineru_image_content_needs_review"],
                }
            )

    formula_blocks = FORMULA_BLOCK_RE.findall(markdown)
    return {
        "schema_version": "mineru_evidence_seed.v2",
        "created_at": now_iso(),
        "source_pdf": str(source_pdf) if source_pdf else None,
        "auto_dir": str(auto_dir),
        "first_page_number": first_page_number,
        "artifacts": artifacts,
        "counts": {
            "content_items": len(items),
            "type_counts": dict(sorted(type_counts.items())),
            "pages_local": pages,
            "pages_physical": [page + first_page_number for page in pages],
            "image_files": len(image_files),
            "image_bytes": sum(path.stat().st_size for path in image_files if path.is_file()),
            "markdown_chars": len(markdown),
            "markdown_formula_blocks": len(formula_blocks),
            "markdown_image_refs": len(IMAGE_REF_RE.findall(markdown)),
        },
        "blocks": blocks,
        "formula_candidates": formula_candidates,
        "table_candidates": table_candidates,
        "image_candidates": image_candidates,
    }


def load_content_items(auto_dir: Path) -> tuple[Path, list[dict[str, Any]]]:
    content_list_path = find_one(auto_dir, "_content_list.json")
    if content_list_path is None:
        raise SystemExit(f"MinerU content_list not found in: {auto_dir}")
    payload = read_json(content_list_path)
    if not isinstance(payload, list):
        raise SystemExit(f"MinerU content_list is not a list: {content_list_path}")
    return content_list_path, payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Adapt MinerU output into pipeline raw text/report inputs")
    parser.add_argument("--auto-dir", required=True)
    parser.add_argument("--source-pdf", required=True)
    parser.add_argument("--first-page-number", type=int, default=1)
    parser.add_argument("--output-raw-text", required=True)
    parser.add_argument("--output-report-json", required=True)
    parser.add_argument("--output-seed-json", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    auto_dir = resolve_path(args.auto_dir, required=True)
    source_pdf = resolve_path(args.source_pdf, required=True)
    output_raw_text = resolve_path(args.output_raw_text)
    output_report_json = resolve_path(args.output_report_json)
    output_seed_json = resolve_path(args.output_seed_json)
    if auto_dir is None or source_pdf is None or output_raw_text is None or output_report_json is None or output_seed_json is None:
        raise SystemExit("Required paths could not be resolved.")

    print(f"Resolved MinerU auto dir: {auto_dir}")
    print(f"Resolved source PDF: {source_pdf}")
    print(f"Resolved raw text output: {output_raw_text}")
    print(f"Resolved report output: {output_report_json}")
    print(f"Resolved seed output: {output_seed_json}")

    _content_list_path, items = load_content_items(auto_dir)
    artifacts = artifact_paths(auto_dir)
    raw_text = build_raw_text(items, first_page_number=args.first_page_number)
    report = build_report(items, source_pdf, args.first_page_number, artifacts)
    seed = build_seed(items, auto_dir, source_pdf, args.first_page_number, artifacts)

    output_raw_text.parent.mkdir(parents=True, exist_ok=True)
    output_raw_text.write_text(raw_text, encoding="utf-8")
    write_json(output_report_json, report)
    write_json(output_seed_json, seed)

    print(f"Raw text written: {output_raw_text}")
    print(f"Report JSON written: {output_report_json}")
    print(f"MinerU seed JSON written: {output_seed_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
