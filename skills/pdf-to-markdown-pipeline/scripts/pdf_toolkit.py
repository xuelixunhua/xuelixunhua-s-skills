#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Accuracy-first PDF helper for the Mengxi rules workspace.

Features:
1. inspect: print resolved path, metadata, page count, and text quality hints
2. split: split a PDF into page ranges using pypdf
3. extract: extract page text with per-page quality scoring

Examples:
  py pdf_toolkit.py inspect --input ..\\..\\01_规则原文\\2026版\\蒙西规则-2026年-现货.pdf
  py pdf_toolkit.py split --input ..\\..\\01_规则原文\\2026版\\蒙西规则-2026年.pdf --output-dir ..\\..\\01_规则原文\\2026版 --range 现货:81-180
  py pdf_toolkit.py extract --input ..\\..\\01_规则原文\\2026版\\蒙西规则-2026年-现货.pdf --output-text ..\\..\\tmp\\pdfs\\mx_2026_spot_raw.txt --output-json ..\\..\\tmp\\pdfs\\mx_2026_spot_report.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

from formula_multimodal import review_page_with_multimodal


CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
INLINE_PAGE_FOOTER_RE = re.compile(r"第\s*\d+\s*页\s*[,，]\s*共\s*\d+\s*页")
INLINE_QQ_ARTIFACT_RE = re.compile(r"\{\s*,?\s*\d+.{0,24}?Qq\s*\d+.{0,8}?榰")
INLINE_TIMESTAMP_WATERMARK_RE = re.compile(
    r"(?:郑书杰|葫芦岛元亨能源有限公司)\s*20\d{2}年\d{1,2}月\d{1,2}日\s*\d{1,2}:\d{2}:\d{2}"
)
INLINE_BARE_TIMESTAMP_WATERMARK_RE = re.compile(
    r"20\d{2}年\d{1,2}月\d{1,2}日\s*\d{1,2}:\d{2}:\d{2}"
)
INLINE_WATERMARK_TEXT_RE = re.compile(r"(?:郑书杰|葫芦岛元亨能源有限(?:公司)?)")
SYMBOL_FONT_GLYPH_MAP = {
    "\uf020": " ",
    "\uf022": "\u2200",  # forall
    "\uf028": "(",
    "\uf029": ")",
    "\uf02b": "+",
    "\uf02d": "-",
    "\uf03c": "<",
    "\uf03d": "=",
    "\uf03e": ">",
    "\uf044": "\u0394",
    "\uf061": "\u03b1",
    "\uf062": "\u03b2",
    "\uf064": "\u03b4",
    "\uf065": "\u03b5",
    "\uf067": "\u03b3",
    "\uf068": "\u03b7",
    "\uf06c": "\u03bb",
    "\uf06d": "\u03bc",
    "\uf06e": "\u03bd",
    "\uf072": "\u03c1",
    "\uf073": "\u03c3",
    "\uf074": "\u03c4",
    "\uf0a2": "\u2032",
    "\uf0a3": "\u2264",
    "\uf0b1": "\u00b1",
    "\uf0b3": "\u2265",
    "\uf0b4": "\u00d7",
    "\uf0ce": "\u2208",
    "\uf0e5": "\u2211",
    "\uf0e6": "(",
    "\uf0e7": "(",
    "\uf0e8": "(",
    "\uf0e9": "[",
    "\uf0ea": "[",
    "\uf0eb": "[",
    "\uf0ec": "{",
    "\uf0ed": "{",
    "\uf0ee": "{",
    "\uf0ef": "{",
    "\uf0f2": "\u222b",
    "\uf0f6": ")",
    "\uf0f7": ")",
    "\uf0f8": ")",
    "\uf0f9": "]",
    "\uf0fa": "]",
    "\uf0fb": "]",
    "\uf0fc": "}",
    "\uf0fd": "}",
    "\uf0fe": "}",
}
SYMBOL_FONT_GLYPH_TRANSLATION = str.maketrans(SYMBOL_FONT_GLYPH_MAP)
LEGACY_FORMULA_GLYPH_RE = re.compile(
    "[" + re.escape("".join(SYMBOL_FONT_GLYPH_MAP.keys())) + "]"
)
GARBLED_FORMULA_TOKEN_RE = re.compile(r"(?:PQPQR|PQR|QRP|QRR|QPQ|PQQ)")
ASCII_TOKEN_SOUP_RE = re.compile(
    r"(?:(?<![A-Za-z])[A-Za-z]{1,4}(?![A-Za-z])\s+){6,}(?<![A-Za-z])[A-Za-z]{0,4}"
)
FOOTER_TEXT_COMPACT_RE = re.compile(r"^第\d+页[,，]?共\d+页$")
PHYSICAL_PAGE_COMPACT_RE = re.compile(r"^[-—]\d+[-—]$")


def require_pypdf():
    try:
        from pypdf import PdfReader, PdfWriter
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "pypdf is required. Please install it in the Python environment used for this workspace."
        ) from exc
    return PdfReader, PdfWriter


def require_visual_stack():
    try:
        import fitz
    except Exception as exc:  # pragma: no cover
        raise SystemExit(
            "PyMuPDF (fitz) is required for page rendering / OCR review."
        ) from exc
    return fitz


def resolve_input_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if not path.exists():
        raise SystemExit(f"Input file does not exist: {path}")
    return path


def resolve_output_path(raw_path: str | None) -> Path | None:
    if raw_path is None:
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def printable_ratio(text: str) -> float:
    if not text:
        return 0.0
    printable = sum(1 for ch in text if ch.isprintable() or ch in "\n\r\t")
    return printable / max(len(text), 1)


def cjk_ratio(text: str) -> float:
    if not text:
        return 0.0
    cjk = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
    return cjk / max(len(text), 1)


def surrogate_count(text: str) -> int:
    return sum(1 for ch in text if 0xD800 <= ord(ch) <= 0xDFFF)


def sanitize_text(text: str) -> str:
    if not text:
        return ""
    cleaned = text.encode("utf-8", errors="replace").decode("utf-8")
    cleaned = CONTROL_CHAR_RE.sub("", cleaned)
    cleaned = cleaned.translate(SYMBOL_FONT_GLYPH_TRANSLATION)
    cleaned = INLINE_TIMESTAMP_WATERMARK_RE.sub(" ", cleaned)
    cleaned = INLINE_BARE_TIMESTAMP_WATERMARK_RE.sub(" ", cleaned)
    return INLINE_WATERMARK_TEXT_RE.sub(" ", cleaned)


def contains_inline_page_artifact(text: str) -> bool:
    if not text:
        return False
    return bool(
        INLINE_PAGE_FOOTER_RE.search(text)
        or INLINE_QQ_ARTIFACT_RE.search(text)
        or INLINE_TIMESTAMP_WATERMARK_RE.search(text)
        or INLINE_BARE_TIMESTAMP_WATERMARK_RE.search(text)
        or INLINE_WATERMARK_TEXT_RE.search(text)
    )


def compact_block_text(text: str) -> str:
    return re.sub(r"\s+", "", sanitize_text(text))


def is_footer_block_text(text: str) -> bool:
    compact = compact_block_text(text)
    if not compact:
        return False
    return bool(
        FOOTER_TEXT_COMPACT_RE.match(compact)
        or PHYSICAL_PAGE_COMPACT_RE.match(compact)
    )


def is_header_block_text(text: str) -> bool:
    compact = compact_block_text(text)
    if not compact or len(compact) > 80:
        return False
    return any(token in compact for token in ("内蒙古电力市场", "实施细则", "基本规则"))


def formula_noise_score(text: str) -> int:
    if not text:
        return 0
    formula_tokens = len(re.findall(r"[=+\-*/%<>∑ΣΠπΔλβμ±÷]", text))
    legacy_glyphs = len(LEGACY_FORMULA_GLYPH_RE.findall(text))
    private_use_chars = sum(1 for ch in text if 0xE000 <= ord(ch) <= 0xF8FF)
    uppercase_runs = len(re.findall(r"\b[A-Z]{4,}\b", text))
    token_soup_bonus = 6 if ASCII_TOKEN_SOUP_RE.search(text) else 0
    garbled_tokens = len(GARBLED_FORMULA_TOKEN_RE.findall(text))
    return (
        formula_tokens
        + legacy_glyphs * 3
        + private_use_chars * 4
        + uppercase_runs * 2
        + token_soup_bonus
        + garbled_tokens * 5
    )


def looks_formula_heavy(text: str) -> bool:
    if not text:
        return False
    score = formula_noise_score(text)
    if score >= 12:
        return True
    if LEGACY_FORMULA_GLYPH_RE.search(text) and score >= 8:
        return True
    if GARBLED_FORMULA_TOKEN_RE.search(text):
        return True
    return False


def score_page_text(text: str) -> dict:
    stripped = text.strip()
    char_count = len(stripped)
    lines = [line for line in stripped.splitlines() if line.strip()]
    replacement_count = stripped.count("\ufffd")
    surrogate_chars = surrogate_count(stripped)
    pr = printable_ratio(stripped)
    cr = cjk_ratio(stripped)

    flags: List[str] = []
    if char_count < 30:
        flags.append("very_low_text")
    if pr < 0.85:
        flags.append("non_printable_noise")
    if replacement_count > 0:
        flags.append("replacement_characters")
    if surrogate_chars > 0:
        flags.append("surrogate_characters")
    if looks_formula_heavy(stripped):
        flags.append("formula_like_page")
    if contains_inline_page_artifact(stripped):
        flags.append("inline_page_artifacts")

    likely_needs_ocr = (
        "very_low_text" in flags
        or "replacement_characters" in flags
        or "surrogate_characters" in flags
        or "non_printable_noise" in flags
    )

    if likely_needs_ocr and looks_formula_heavy(stripped):
        suggested_action = "ocr_and_formula_review"
    elif likely_needs_ocr:
        suggested_action = "ocr_review"
    elif looks_formula_heavy(stripped):
        suggested_action = "formula_review"
    else:
        suggested_action = "native_text_ok"

    return {
        "char_count": char_count,
        "line_count": len(lines),
        "printable_ratio": round(pr, 4),
        "cjk_ratio": round(cr, 4),
        "replacement_count": replacement_count,
        "surrogate_count": surrogate_chars,
        "formula_like": looks_formula_heavy(stripped),
        "likely_needs_ocr": likely_needs_ocr,
        "suggested_action": suggested_action,
        "flags": flags,
    }


def extract_page_text_with_layout(page) -> str:
    rect = page.rect
    left = rect.x0 + rect.width * 0.03
    right = rect.x1 - rect.width * 0.03
    top = rect.y0 + rect.height * 0.03
    bottom = rect.y1 - rect.height * 0.05
    all_blocks = page.get_text("blocks")
    for block in all_blocks:
        if len(block) < 5:
            continue
        x0, y0, x1, y1, text = block[:5]
        block_type = block[6] if len(block) > 6 else 0
        if block_type != 0:
            continue
        if is_footer_block_text(text):
            bottom = min(bottom, y0 - 4)
        elif y0 <= rect.y0 + rect.height * 0.08 and is_header_block_text(text):
            top = max(top, y1 + 4)
    clip = rect if right <= left or bottom <= top else (left, top, right, bottom)

    blocks = page.get_text("blocks", clip=clip)
    ordered_blocks = []
    for block in blocks:
        if len(block) < 5:
            continue
        x0, y0, x1, y1, text = block[:5]
        block_type = block[6] if len(block) > 6 else 0
        if block_type != 0:
            continue
        if is_footer_block_text(text):
            continue
        cleaned = sanitize_text(text).strip()
        if not cleaned:
            continue
        ordered_blocks.append((round(y0, 1), round(x0, 1), cleaned))
    ordered_blocks.sort(key=lambda item: (item[0], item[1]))
    return "\n".join(item[2] for item in ordered_blocks)


def score_penalty(score: dict) -> int:
    penalty = len(score["flags"])
    if "inline_page_artifacts" in score["flags"]:
        penalty += 4
    if "formula_like_page" in score["flags"]:
        penalty += 1
    return penalty


def should_replace_with_layout(native_score: dict, layout_score: dict) -> bool:
    native_chars = native_score["char_count"]
    layout_chars = layout_score["char_count"]
    if (
        "inline_page_artifacts" in native_score["flags"]
        and "inline_page_artifacts" not in layout_score["flags"]
        and layout_chars >= max(10, int(native_chars * 0.3))
    ):
        return True
    if layout_chars < max(30, int(native_chars * 0.5)):
        return False
    if score_penalty(layout_score) + 1 < score_penalty(native_score):
        return True
    if (
        layout_score["printable_ratio"] > native_score["printable_ratio"]
        and layout_chars >= max(30, int(native_chars * 0.7))
    ):
        return True
    return False


def summarize_document_strategy(page_reports: List[dict]) -> dict:
    total_pages = len(page_reports)
    ocr_pages = [item["page"] for item in page_reports if item["likely_needs_ocr"]]
    formula_pages = [item["page"] for item in page_reports if item["formula_like"]]
    combined_pages = [
        item["page"]
        for item in page_reports
        if item["suggested_action"] == "ocr_and_formula_review"
    ]

    if total_pages == 0:
        document_type = "unknown"
    elif len(ocr_pages) / total_pages >= 0.5:
        document_type = "scan_or_ocr_heavy_pdf"
    elif formula_pages:
        document_type = "text_pdf_with_formula_pages"
    else:
        document_type = "text_pdf"

    if document_type == "scan_or_ocr_heavy_pdf":
        recommended_pipeline = "ocr_first_with_manual_review"
    elif combined_pages or formula_pages:
        recommended_pipeline = "native_text_first_with_targeted_formula_review"
    else:
        recommended_pipeline = "native_text_first"

    return {
        "document_type_guess": document_type,
        "recommended_pipeline": recommended_pipeline,
        "ocr_review_page_count": len(ocr_pages),
        "formula_review_page_count": len(formula_pages),
        "ocr_review_pages": ocr_pages,
        "formula_review_pages": formula_pages,
        "ocr_and_formula_review_pages": combined_pages,
    }


def page_slice(total_pages: int, start: int | None, end: int | None) -> Tuple[int, int]:
    start_page = 1 if start is None else start
    end_page = total_pages if end is None else end
    if start_page < 1 or end_page < start_page or end_page > total_pages:
        raise SystemExit(
            f"Invalid page range: {start_page}-{end_page}, total pages: {total_pages}"
        )
    return start_page, end_page


def parse_ranges(range_args: Iterable[str]) -> List[Tuple[str, int, int]]:
    parsed = []
    for item in range_args:
        if ":" not in item or "-" not in item:
            raise SystemExit(f"Invalid --range value: {item}. Expected name:start-end")
        name, page_part = item.split(":", 1)
        start_text, end_text = page_part.split("-", 1)
        start_page = int(start_text)
        end_page = int(end_text)
        if not name.strip():
            raise SystemExit(f"Invalid range name in: {item}")
        parsed.append((name.strip(), start_page, end_page))
    return parsed


def parse_page_list(raw_value: str | None) -> List[int]:
    if not raw_value:
        return []
    pages: List[int] = []
    for chunk in raw_value.split(","):
        value = chunk.strip()
        if not value:
            continue
        pages.append(int(value))
    return sorted(set(pages))


def inspect_pdf(args: argparse.Namespace) -> int:
    PdfReader, _ = require_pypdf()
    input_path = resolve_input_path(args.input)
    print(f"Resolved input: {input_path}")

    reader = PdfReader(str(input_path))
    total_pages = len(reader.pages)
    print(f"Total pages: {total_pages}")

    if reader.metadata:
        print("Metadata:")
        for key, value in sorted(reader.metadata.items()):
            print(f"  {key}: {value}")

    sample_limit = min(args.sample_pages, total_pages)
    print(f"Sampling first {sample_limit} pages for text quality:")
    for index in range(sample_limit):
        text = reader.pages[index].extract_text() or ""
        score = score_page_text(text)
        print(
            f"  Page {index + 1}: chars={score['char_count']} "
            f"flags={','.join(score['flags']) or 'ok'}"
        )
    return 0


def split_pdf(args: argparse.Namespace) -> int:
    PdfReader, PdfWriter = require_pypdf()
    input_path = resolve_input_path(args.input)
    output_dir = resolve_output_path(args.output_dir)
    if output_dir is None:
        raise SystemExit("--output-dir is required for split")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Resolved input: {input_path}")
    print(f"Resolved output dir: {output_dir}")

    reader = PdfReader(str(input_path))
    total_pages = len(reader.pages)
    ranges = parse_ranges(args.range)

    for name, start_page, end_page in ranges:
        checked_start, checked_end = page_slice(total_pages, start_page, end_page)
        writer = PdfWriter()
        for page_number in range(checked_start - 1, checked_end):
            writer.add_page(reader.pages[page_number])
        if reader.metadata:
            writer.add_metadata(reader.metadata)

        output_path = output_dir / f"{name}.pdf"
        print(f"Writing {output_path} from pages {checked_start}-{checked_end}")
        with output_path.open("wb") as handle:
            writer.write(handle)

    return 0


def extract_pdf_text(args: argparse.Namespace) -> int:
    PdfReader, _ = require_pypdf()
    input_path = resolve_input_path(args.input)
    output_text = resolve_output_path(args.output_text)
    output_json = resolve_output_path(args.output_json)

    if output_text is None or output_json is None:
        raise SystemExit("--output-text and --output-json are required for extract")

    print(f"Resolved input: {input_path}")
    print(f"Resolved text output: {output_text}")
    print(f"Resolved report output: {output_json}")

    reader = PdfReader(str(input_path))
    fitz = None
    fitz_doc = None
    try:
        fitz = require_visual_stack()
        fitz_doc = fitz.open(str(input_path))
    except SystemExit:
        fitz_doc = None
    total_pages = len(reader.pages)
    start_page, end_page = page_slice(total_pages, args.start_page, args.end_page)

    text_chunks: List[str] = []
    page_reports = []

    try:
        for page_number in range(start_page - 1, end_page):
            page_index = page_number + 1
            raw_text = reader.pages[page_number].extract_text() or ""
            text = sanitize_text(raw_text)
            score = score_page_text(text)
            extraction_engine = "pypdf_native"
            layout_cleanup_applied = False

            if fitz_doc is not None and (
                "inline_page_artifacts" in score["flags"]
                or "non_printable_noise" in score["flags"]
                or "replacement_characters" in score["flags"]
            ):
                layout_page = fitz_doc.load_page(page_number)
                layout_text = extract_page_text_with_layout(layout_page)
                layout_score = score_page_text(layout_text)
                if should_replace_with_layout(score, layout_score):
                    text = layout_text
                    score = layout_score
                    extraction_engine = "pypdf_with_fitz_layout_cleanup"
                    layout_cleanup_applied = True

            page_reports.append(
                {
                    "page": page_index,
                    "extraction_engine": extraction_engine,
                    "layout_cleanup_applied": layout_cleanup_applied,
                    **score,
                }
            )

            text_chunks.append("=" * 60)
            text_chunks.append(f"PAGE {page_index}")
            text_chunks.append("=" * 60)
            text_chunks.append(text.rstrip())
            text_chunks.append("")
    finally:
        if fitz_doc is not None:
            fitz_doc.close()

    output_text.write_text("\n".join(text_chunks), encoding="utf-8")

    report = {
        "input_path": str(input_path),
        "page_range": [start_page, end_page],
        "total_pages_in_document": total_pages,
        "pages_requiring_ocr_review": [
            item["page"] for item in page_reports if item["likely_needs_ocr"]
        ],
        "formula_like_pages": [
            item["page"] for item in page_reports if item["formula_like"]
        ],
        "pages_requiring_formula_review": [
            item["page"]
            for item in page_reports
            if item["suggested_action"] in ("formula_review", "ocr_and_formula_review")
        ],
        "document_strategy": summarize_document_strategy(page_reports),
        "page_reports": page_reports,
    }
    output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    flagged = report["pages_requiring_ocr_review"]
    print(f"Extracted pages {start_page}-{end_page}")
    print(f"OCR review pages: {flagged if flagged else 'none'}")
    print(
        "Recommended pipeline: "
        f"{report['document_strategy']['recommended_pipeline']}"
    )
    return 0


def render_review_pages(args: argparse.Namespace) -> int:
    fitz = require_visual_stack()
    input_path = resolve_input_path(args.input)
    report_path = resolve_input_path(args.report_json) if args.report_json else None
    output_dir = resolve_output_path(args.output_dir)
    if output_dir is None:
        raise SystemExit("--output-dir is required for review-pages")
    output_dir.mkdir(parents=True, exist_ok=True)

    pages = parse_page_list(args.pages)
    if not pages and report_path:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        pages = report.get("pages_requiring_formula_review", [])
    if not pages:
        raise SystemExit("No review pages resolved. Pass --pages or provide a report JSON with formula review pages.")

    print(f"Resolved input: {input_path}")
    if report_path:
        print(f"Resolved report: {report_path}")
    print(f"Resolved output dir: {output_dir}")
    print(f"Review pages: {pages}")
    print(f"OCR engine: {args.ocr_engine}")

    doc = fitz.open(str(input_path))
    records = []
    for page_number in pages:
        if page_number < 1 or page_number > len(doc):
            print(f"Skip page {page_number}: out of range")
            continue
        page = doc.load_page(page_number - 1)
        matrix = fitz.Matrix(args.dpi / 72, args.dpi / 72)
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        image_path = output_dir / f"page_{page_number:03d}.png"
        pix.save(str(image_path))

        ocr_text = ""
        review_required = False
        issues: List[str] = []
        raw_response_path = None
        if args.ocr_engine == "multimodal":
            try:
                mm_result = review_page_with_multimodal(
                    image_path=image_path,
                    page_number=page_number,
                    document={"title": input_path.stem},
                )
                ocr_text = mm_result.get("page_markdown", "")
                review_required = bool(mm_result.get("review_required"))
                issues = mm_result.get("issues", []) or []
                raw_response = mm_result.get("raw_response", "")
                if raw_response:
                    raw_response_path = output_dir / f"page_{page_number:03d}_ocr_raw.json"
                    raw_response_path.write_text(raw_response, encoding="utf-8")
            except Exception as exc:  # pragma: no cover
                review_required = True
                issues = [f"多模态页面识别失败：{exc}"]
                ocr_text = ""
            ocr_path = output_dir / f"page_{page_number:03d}_ocr.md"
        elif args.ocr_engine == "tesseract":
            image = None
            try:
                import pytesseract
                from PIL import Image

                image = Image.open(image_path)
                ocr_text = pytesseract.image_to_string(
                    image,
                    lang=args.ocr_lang,
                    config="--psm 6",
                )
            except Exception as exc:  # pragma: no cover
                review_required = True
                issues = [f"Tesseract OCR failed: {exc}"]
                ocr_text = f"[OCR failed] {exc}"
            finally:
                if image is not None:
                    image.close()
            ocr_path = output_dir / f"page_{page_number:03d}_ocr.txt"
        else:
            review_required = True
            issues = ["仅输出页面截图，未执行 OCR。"]
            ocr_path = output_dir / f"page_{page_number:03d}_ocr.txt"

        ocr_path.write_text(ocr_text, encoding="utf-8")
        records.append(
            {
                "page": page_number,
                "image_path": str(image_path),
                "ocr_output_path": str(ocr_path),
                "ocr_engine": args.ocr_engine,
                "ocr_format": "markdown" if ocr_path.suffix.lower() == ".md" else "text",
                "ocr_char_count": len(ocr_text.strip()),
                "review_required": review_required,
                "issues": issues,
                "raw_response_path": str(raw_response_path) if raw_response_path else None,
            }
        )

    summary = {
        "input_path": str(input_path),
        "report_path": str(report_path) if report_path else None,
        "pages": pages,
        "dpi": args.dpi,
        "ocr_engine": args.ocr_engine,
        "ocr_lang": args.ocr_lang,
        "records": records,
    }
    summary_path = output_dir / "review_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Rendered pages: {len(records)}")
    print(f"Review summary: {summary_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="General PDF helper for the Mengxi workspace")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect PDF metadata and text quality")
    inspect_parser.add_argument("--input", required=True, help="Input PDF path")
    inspect_parser.add_argument("--sample-pages", type=int, default=5, help="Pages to sample")
    inspect_parser.set_defaults(func=inspect_pdf)

    split_parser = subparsers.add_parser("split", help="Split PDF by page ranges")
    split_parser.add_argument("--input", required=True, help="Input PDF path")
    split_parser.add_argument("--output-dir", required=True, help="Output directory")
    split_parser.add_argument(
        "--range",
        action="append",
        default=[],
        help="Page range in the form name:start-end. Repeat for multiple outputs.",
    )
    split_parser.set_defaults(func=split_pdf)

    extract_parser = subparsers.add_parser("extract", help="Extract text and quality report")
    extract_parser.add_argument("--input", required=True, help="Input PDF path")
    extract_parser.add_argument("--output-text", required=True, help="Path for extracted text")
    extract_parser.add_argument("--output-json", required=True, help="Path for quality report JSON")
    extract_parser.add_argument("--start-page", type=int, help="1-based start page")
    extract_parser.add_argument("--end-page", type=int, help="1-based end page")
    extract_parser.set_defaults(func=extract_pdf_text)

    review_parser = subparsers.add_parser(
        "review-pages",
        help="Render review pages to PNG and run multimodal OCR / OCR review for formula inspection",
    )
    review_parser.add_argument("--input", required=True, help="Input PDF path")
    review_parser.add_argument("--report-json", help="Quality report JSON; used to resolve formula review pages")
    review_parser.add_argument("--output-dir", required=True, help="Output directory under tmp/pdfs/")
    review_parser.add_argument("--pages", help="Comma-separated 1-based pages to review")
    review_parser.add_argument("--dpi", type=int, default=220, help="Render DPI")
    review_parser.add_argument(
        "--ocr-engine",
        choices=["multimodal", "tesseract", "none"],
        default="multimodal",
        help="OCR engine for review text. Recommend multimodal for formula pages.",
    )
    review_parser.add_argument("--ocr-lang", default="chi_sim+eng", help="Tesseract language pack")
    review_parser.set_defaults(func=render_review_pages)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
