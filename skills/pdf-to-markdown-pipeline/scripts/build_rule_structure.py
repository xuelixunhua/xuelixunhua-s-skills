#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a first-pass structured JSON and Markdown review file from extracted rule text.

This builder intentionally focuses on the minimal stable objects observed in the
Mengxi spot rule sample:
1. document metadata
2. toc entries
3. section nodes (chapter / section / appendix)
4. clauses
5. appendix blocks
6. page-quality summary
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from formula_multimodal import apply_formula_markdown, review_pdf_pages_with_multimodal


PAGE_MARKER_RE = re.compile(r"^PAGE\s+(\d+)\s*$")
FOOTER_RE = re.compile(r"^第\d+页,共\d+页$")
PHYSICAL_PAGE_RE = re.compile(r"^—\s*\d+\s*—$")
CHAPTER_RE = re.compile(r"^(第[一二三四五六七八九十百零]+章)\s*(.+)$")
SECTION_RE = re.compile(r"^(第[一二三四五六七八九十百零]+节)\s*(.+)$")
CLAUSE_RE = re.compile(r"^(第[一二三四五六七八九十百零]+条)\s*(.*)$")
APPENDIX_RE = re.compile(r"^(附录|附件)\s*([0-9一二三四五六七八九十]+)\s*[：:、]?\s*(.+)$")
TITLE_LINE_RE = re.compile(r"(基本规则|实施细则)(（[^）]+）)?$")
TOC_ENTRY_RE = re.compile(
    r"^((?:第[一二三四五六七八九十百零]+章)|(?:第[一二三四五六七八九十百零]+节)|(?:(?:附录|附件)\s*[0-9一二三四五六七八九十]+)|(?:(?:附录|附件)[0-9一二三四五六七八九十]+))\s*(.*?)\.{2,}\s*(\d+)$"
)
TOC_ENTRY_FALLBACK_RE = re.compile(
    r"^((?:第[一二三四五六七八九十百零]+章)|(?:第[一二三四五六七八九十百零]+节)|(?:(?:附录|附件)\s*[0-9一二三四五六七八九十]+)|(?:(?:附录|附件)[0-9一二三四五六七八九十]+))\s*(.*?)\s+(\d+)$"
)
CLAUSE_LABEL_RE = re.compile(r"^\[([^\]]+)\]")
APPENDIX_REF_RE = re.compile(r"(附录|附件)\s*([0-9一二三四五六七八九十]+)")
NUMERIC_HEADING_RE = re.compile(
    r"^([0-9]{1,2}(?:\.[0-9]{1,2})*)(?:\s+|\s*(?=[\u4e00-\u9fff]))(.+?)$"
)
NUMERIC_MARKER_ONLY_RE = re.compile(r"^[0-9]{1,2}(?:\.[0-9]{1,2})*$")
FORMULA_HEADING_SYMBOL_RE = re.compile(r"[=+\-*/%<>∑ΣΠπΔλβμ±÷×∫≤≥\[\]{}]")
FORMULA_HEADING_LATIN_TOKEN_RE = re.compile(r"(?<![A-Za-z])[A-Za-z][A-Za-z0-9_]{0,5}(?![A-Za-z])")
FORMULA_HEADING_CODE_PREFIX_RE = re.compile(r"^[A-Z][A-Za-z0-9_]{0,8}\s+")
TOC_DOT_RE = re.compile(r"\.{2,}|…{2,}")
FORMULA_CONTEXT_RE = re.compile(r"(计算公式|具体公式|公式如下|公式为|分摊返还方式|求和|返还方式)")
FORMULA_SYMBOL_RE = re.compile(r"[=+\-*/%<>∑ΣΠπΔλβμ±÷×]")
SINGLE_LETTER_TOKEN_RE = re.compile(r"(?<![A-Za-z])[A-Za-z](?![A-Za-z])")
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
MULTILINE_FOOTER_FRAGMENT_RE = re.compile(
    r"^(?:(?:\d+[-—]{1,4})|(?:[-—]{1,2}\d+[-—]{1,2}))?第\d+页[,，]?共\d+页$"
)
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
APPENDIX_PAGE_REVIEW_KINDS = {"parameter", "formula_model"}
TABULAR_RULE_TYPES = {"regional_transmission_tariff", "provincial_grid_tariff"}


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def sanitize_line(line: str) -> str:
    cleaned = CONTROL_CHAR_RE.sub("", str(line or "").replace("\x00", ""))
    cleaned = strip_inline_artifacts(cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()


def normalize_symbol_font_glyphs(text: str) -> str:
    return str(text or "").translate(SYMBOL_FONT_GLYPH_TRANSLATION)


def strip_inline_artifacts(text: str) -> str:
    cleaned = normalize_symbol_font_glyphs(text)
    cleaned = INLINE_PAGE_FOOTER_RE.sub(" ", cleaned)
    cleaned = INLINE_QQ_ARTIFACT_RE.sub(" ", cleaned)
    cleaned = INLINE_TIMESTAMP_WATERMARK_RE.sub(" ", cleaned)
    cleaned = INLINE_BARE_TIMESTAMP_WATERMARK_RE.sub(" ", cleaned)
    cleaned = INLINE_WATERMARK_TEXT_RE.sub(" ", cleaned)
    cleaned = re.sub(r"—\s*\d+\s*—", " ", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip()


def clean_issue_for_markdown(text: str) -> str:
    cleaned = strip_inline_artifacts(text)
    cleaned = cleaned.replace("“”", "")
    cleaned = re.sub(r"图片底部显示[，,、及\s]*", "图片底部存在页码信息，", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(" ，,、。")


def is_non_content_page_issue(text: str) -> bool:
    """Drop viewer/page-number diagnostics from the final AI-readable structure."""
    cleaned = str(text or "")
    page_terms = ("页码显示", "图片底部显示", "页面底部显示", "物理页码", "PDF阅读器页码")
    mismatch_terms = ("任务给定物理页", "文档内编页", "页码不同", "页码为")
    return any(term in cleaned for term in page_terms) and any(term in cleaned for term in mismatch_terms)


def clean_issues_for_structure(issues: List[str]) -> List[str]:
    cleaned_issues: List[str] = []
    for issue in issues:
        if is_non_content_page_issue(issue):
            continue
        cleaned = clean_issue_for_markdown(issue)
        if cleaned:
            cleaned_issues.append(cleaned)
    return dedupe_preserve_order(cleaned_issues)


def compact_line_token(line: str) -> str:
    return re.sub(r"\s+", "", str(line or ""))


def normalize_page_lines(lines: List[str]) -> List[str]:
    normalized: List[str] = []
    index = 0
    total = len(lines)

    while index < total:
        matched = False
        max_window = min(8, total - index)
        for window_size in range(max_window, 1, -1):
            chunk = [compact_line_token(item) for item in lines[index : index + window_size]]
            compact = "".join(token for token in chunk if token)
            if compact and MULTILINE_FOOTER_FRAGMENT_RE.match(compact):
                index += window_size
                matched = True
                break
        if matched:
            continue
        normalized.append(lines[index])
        index += 1

    return normalized


def looks_like_title_line(line: str) -> bool:
    compact = line.replace(" ", "").strip()
    if not compact or not TITLE_LINE_RE.search(compact):
        return False
    if len(compact) > 40:
        return False
    if "." in compact or "…" in compact or "..." in compact:
        return False
    if compact.startswith("第") and "条" in compact:
        return False
    return True


def is_toc_like_line(line: str) -> bool:
    return bool(TOC_DOT_RE.search(str(line or "")))


def looks_formula_or_table_heading(line: str) -> bool:
    compact = str(line or "").strip()
    if not compact:
        return False
    latin_tokens = FORMULA_HEADING_LATIN_TOKEN_RE.findall(compact)
    if FORMULA_HEADING_SYMBOL_RE.search(compact) and len(latin_tokens) >= 1:
        return True
    if len(latin_tokens) >= 4:
        return True
    if FORMULA_HEADING_CODE_PREFIX_RE.match(compact) and latin_tokens:
        first_token = latin_tokens[0]
        if re.search(r"\d", first_token) or first_token in {
            "P",
            "Q",
            "R",
            "C",
            "M",
            "E",
            "LMP",
            "MAX",
            "MIN",
        }:
            return True
    if FORMULA_HEADING_CODE_PREFIX_RE.match(compact) and len(latin_tokens) >= 2:
        return True
    return False


def looks_numeric_heading_title(line: str) -> bool:
    compact = str(line or "").strip()
    if not compact or len(compact) > 80:
        return False
    if compact in {"目录", "总目录", "目 录", "总 目 录"}:
        return False
    if is_toc_like_line(compact):
        return False
    if NUMERIC_MARKER_ONLY_RE.match(compact):
        return False
    if APPENDIX_RE.match(compact):
        return False
    if looks_formula_or_table_heading(compact):
        return False
    return bool(re.search(r"[\u4e00-\u9fff]", compact))


def merge_numeric_heading_lines(lines: List[str]) -> List[str]:
    merged: List[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        if NUMERIC_MARKER_ONLY_RE.match(line) and looks_numeric_heading_title(next_line):
            merged.append(f"{line} {next_line}")
            index += 2
            continue
        merged.append(line)
        index += 1
    return merged


def parse_numeric_heading(line: str) -> Optional[Tuple[str, str]]:
    if is_toc_like_line(line):
        return None
    match = NUMERIC_HEADING_RE.match(line)
    if not match:
        return None
    title = match.group(2).strip(" ：，、")
    if not looks_numeric_heading_title(title):
        return None
    return match.group(1), title


def printable_ratio(text: str) -> float:
    if not text:
        return 0.0
    printable = sum(1 for ch in text if ch.isprintable() or ch in "\n\r\t")
    return printable / max(len(text), 1)


def is_noise_line(line: str) -> bool:
    if not line:
        return True
    if line.startswith("="):
        return True
    if FOOTER_RE.match(line):
        return True
    if PHYSICAL_PAGE_RE.match(line):
        return True
    if printable_ratio(line) < 0.75 and len(line) < 60:
        return True
    return False


def load_pages(raw_text_path: Path) -> List[Dict]:
    lines = raw_text_path.read_text(encoding="utf-8").splitlines()
    pages: List[Dict] = []
    current_page: Optional[int] = None
    current_lines: List[str] = []

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        marker = PAGE_MARKER_RE.match(line.strip())
        if marker:
            if current_page is not None:
                pages.append({"page": current_page, "lines": normalize_page_lines(current_lines)})
            current_page = int(marker.group(1))
            current_lines = []
            continue
        if current_page is None:
            continue
        cleaned = sanitize_line(line)
        if is_noise_line(cleaned):
            continue
        current_lines.append(cleaned)

    if current_page is not None:
        pages.append({"page": current_page, "lines": normalize_page_lines(current_lines)})

    return pages


def detect_document_markers(pages: List[Dict]) -> Dict:
    toc_start_page = None
    body_start_page = None

    for page in pages:
        text = "\n".join(page["lines"])
        if toc_start_page is None and ("目 录" in text or "\n目录\n" in f"\n{text}\n"):
            toc_start_page = page["page"]
        if body_start_page is None and "第一条" in text and "第一章" in text:
            body_start_page = page["page"]

    if body_start_page is None:
        for page in pages:
            if toc_start_page is not None and page["page"] <= toc_start_page:
                continue
            if any(parse_numeric_heading(line) for line in merge_numeric_heading_lines(page["lines"])):
                body_start_page = page["page"]
                break

    title_page = None
    search_limit = body_start_page or len(pages)
    for page in pages:
        if page["page"] >= search_limit:
            break
        if any(looks_like_title_line(line) for line in page["lines"]):
            title_page = page["page"]
            break

    appendix_start_page = None
    for page in pages:
        if body_start_page is not None and page["page"] < body_start_page:
            continue
        if any(APPENDIX_RE.match(line) for line in page["lines"]):
            appendix_start_page = page["page"]
            break

    return {
        "title_page": title_page,
        "toc_start_page": toc_start_page,
        "body_start_page": body_start_page,
        "appendix_start_page": appendix_start_page,
    }


def extract_title(pages: List[Dict], title_page: Optional[int], source_name: str) -> str:
    if title_page is None:
        return source_name.replace(".pdf", "")
    page = next((item for item in pages if item["page"] == title_page), None)
    if not page:
        return source_name.replace(".pdf", "")
    for idx, line in enumerate(page["lines"]):
        if not looks_like_title_line(line):
            continue
        line = line.replace(" ", "")
        for prefix_index in range(idx - 1, max(-1, idx - 4), -1):
            prefix = page["lines"][prefix_index].replace(" ", "")
            if prefix and any(token in prefix for token in ("内蒙古", "电力", "交易市场")):
                return f"{prefix}{line}"
        return line
    return source_name.replace(".pdf", "")


def parse_toc_entries(pages: List[Dict], toc_start_page: Optional[int], body_start_page: Optional[int]) -> List[Dict]:
    if toc_start_page is None or body_start_page is None or body_start_page <= toc_start_page:
        return []
    toc_pages = [page for page in pages if toc_start_page <= page["page"] < body_start_page]
    entries: List[Dict] = []
    for page in toc_pages:
        for line in page["lines"]:
            match = TOC_ENTRY_RE.match(line)
            if not match:
                match = TOC_ENTRY_FALLBACK_RE.match(line)
            if not match:
                continue
            marker, title, target_page = match.groups()
            normalized_marker = marker.replace(" ", "")
            if normalized_marker.startswith(("附录", "附件")):
                entry_type = "appendix"
            elif normalized_marker.endswith("章"):
                entry_type = "chapter"
            else:
                entry_type = "section"
            entries.append(
                {
                    "entry_type": entry_type,
                    "marker": normalized_marker,
                    "title": title.strip(),
                    "target_page": int(target_page),
                    "source_page": page["page"],
                }
            )
    return entries


def compact_text(lines: List[str]) -> str:
    joined = " ".join(line.strip() for line in lines if line.strip())
    joined = re.sub(r"\s+", " ", joined)
    joined = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", joined)
    joined = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[，。；：！？、])", "", joined)
    joined = re.sub(r"(?<=[（《“])\s+", "", joined)
    joined = re.sub(r"\s+(?=[）》”])", "", joined)
    joined = re.sub(r"\s+([,.;:])", r"\1", joined)
    return joined.strip()


def strip_clause_prefix(text: str, marker: str, label: str | None) -> str:
    cleaned = compact_text([text])
    patterns = [rf"^{re.escape(marker)}\s*"]
    if label:
        patterns.extend(
            [
                rf"^{re.escape(marker)}\s*\[{re.escape(label)}\]\s*",
                rf"^{re.escape(marker)}\s*【{re.escape(label)}】\s*",
            ]
        )
    for pattern in patterns:
        updated = re.sub(pattern, "", cleaned)
        if updated != cleaned:
            return updated.strip()
    return cleaned.strip()


def formula_token_score(text: str) -> int:
    if not text:
        return 0
    private_use_chars = sum(1 for ch in text if 0xE000 <= ord(ch) <= 0xF8FF)
    math_symbols = len(FORMULA_SYMBOL_RE.findall(text))
    single_letters = len(SINGLE_LETTER_TOKEN_RE.findall(text))
    legacy_formula_glyphs = len(LEGACY_FORMULA_GLYPH_RE.findall(text))
    garbled_formula_tokens = len(GARBLED_FORMULA_TOKEN_RE.findall(text))
    uppercase_runs = len(re.findall(r"\b[A-Z]{4,}\b", text))
    ascii_token_soup_bonus = 6 if ASCII_TOKEN_SOUP_RE.search(text) else 0
    return (
        private_use_chars * 4
        + math_symbols
        + single_letters
        + legacy_formula_glyphs * 3
        + garbled_formula_tokens * 5
        + uppercase_runs * 2
        + ascii_token_soup_bonus
    )


def looks_formula_sensitive_text(text: str) -> bool:
    if not text:
        return False
    compact = text.strip()
    if not compact:
        return False
    score = formula_token_score(compact)
    if FORMULA_CONTEXT_RE.search(compact) and score >= 6:
        return True
    if GARBLED_FORMULA_TOKEN_RE.search(compact) and score >= 10:
        return True
    if LEGACY_FORMULA_GLYPH_RE.search(compact) and score >= 8:
        return True
    if ASCII_TOKEN_SOUP_RE.search(compact) and score >= 12:
        return True
    if score >= 18:
        return True
    if "）（）（" in compact or "" in compact or "" in compact:
        return True
    return False


def classify_appendix(title: str) -> str:
    if any(token in title for token in ("数学模型", "LMP", "SCUC", "SCED")):
        return "formula_model"
    if "参数" in title:
        return "parameter"
    if "术语定义" in title:
        return "terminology"
    if "参与" in title or "机制" in title or "方式" in title:
        return "rule_extension"
    return "general_appendix"


def build_logical_page_lookup(toc_entries: List[Dict], body_start_page: Optional[int]) -> Dict[int, int]:
    chapter_entries = [item for item in toc_entries if item["entry_type"] == "chapter"]
    if not chapter_entries or body_start_page is None:
        return {}
    first_target_page = min(item["target_page"] for item in chapter_entries)
    offset = body_start_page - first_target_page
    return {entry["target_page"]: entry["target_page"] + offset for entry in toc_entries}


def choose_appendix_start_page(
    mapped_page: Optional[int],
    fallback_page: Optional[int],
    max_page: int,
) -> Optional[int]:
    if (
        fallback_page is not None
        and mapped_page is not None
        and 1 <= fallback_page <= max_page
        and 1 <= mapped_page <= max_page
        and fallback_page <= mapped_page
        and (mapped_page - fallback_page) <= 2
    ):
        return fallback_page
    if mapped_page is not None and 1 <= mapped_page <= max_page:
        if fallback_page is None or abs(mapped_page - fallback_page) <= 3:
            return mapped_page
    if fallback_page is not None and 1 <= fallback_page <= max_page:
        return fallback_page
    if mapped_page is not None and mapped_page >= 1:
        return min(mapped_page, max_page)
    return fallback_page


def enrich_appendices(
    appendices: List[Dict],
    toc_entries: List[Dict],
    pages: List[Dict],
    total_physical_pages: int,
    body_start_page: Optional[int],
    formula_review_pages: List[int],
) -> List[Dict]:
    logical_to_physical = build_logical_page_lookup(toc_entries, body_start_page)
    appendix_toc_entries = [item for item in toc_entries if item["entry_type"] == "appendix"]
    appendix_toc_entries.sort(key=lambda item: item["target_page"])

    pages_by_number = {item["page"]: item for item in pages}
    existing_by_marker = {item["marker"]: item for item in appendices}
    enriched: List[Dict] = []

    for index, toc in enumerate(appendix_toc_entries):
        logical_start = toc["target_page"]
        existing_appendix = existing_by_marker.get(toc["marker"], {})
        physical_start = choose_appendix_start_page(
            logical_to_physical.get(logical_start),
            existing_appendix.get("page"),
            total_physical_pages,
        )
        if physical_start is None:
            continue

        if index + 1 < len(appendix_toc_entries):
            next_logical = appendix_toc_entries[index + 1]["target_page"]
            next_existing = existing_by_marker.get(
                appendix_toc_entries[index + 1]["marker"], {}
            )
            next_physical = choose_appendix_start_page(
                logical_to_physical.get(next_logical),
                next_existing.get("page"),
                total_physical_pages,
            )
            physical_end = (
                next_physical - 1
                if next_physical and next_physical > physical_start
                else total_physical_pages
            )
        else:
            physical_end = total_physical_pages
        physical_end = min(max(physical_end, physical_start), total_physical_pages)

        appendix = existing_appendix.copy()
        appendix["id"] = appendix.get("id", f"appendix-{index + 1:02d}")
        appendix["marker"] = toc["marker"]
        appendix["title"] = appendix.get("title") or toc["title"].strip()
        appendix["page"] = appendix.get("page", physical_start)
        if not appendix.get("content"):
            appendix_lines: List[str] = []
            for page_number in range(physical_start, physical_end + 1):
                page = pages_by_number.get(page_number)
                if not page:
                    continue
                appendix_lines.extend(page["lines"])
            appendix["content"] = compact_text(appendix_lines)
        appendix["start_page"] = appendix.get("start_page", physical_start)
        appendix["appendix_kind"] = classify_appendix(appendix["title"])
        appendix["logical_start_page"] = logical_start
        appendix["physical_start_page"] = physical_start
        appendix["physical_end_page"] = physical_end
        appendix["formula_review_pages"] = [
            page for page in formula_review_pages if physical_start <= page <= physical_end
        ]
        appendix["review_priority"] = (
            "high"
            if appendix["appendix_kind"] == "formula_model" or appendix["formula_review_pages"]
            else "normal"
        )
        enriched.append(appendix)

    if enriched:
        return enriched

    for appendix in appendices:
        appendix["appendix_kind"] = classify_appendix(appendix["title"])
        appendix["logical_start_page"] = None
        appendix["physical_start_page"] = appendix["page"]
        appendix["physical_end_page"] = total_physical_pages
        appendix["formula_review_pages"] = [
            page for page in formula_review_pages if appendix["page"] <= page <= total_physical_pages
        ]
        appendix["review_priority"] = (
            "high"
            if appendix["appendix_kind"] == "formula_model" or appendix["formula_review_pages"]
            else "normal"
        )
    return appendices


def appendix_review_pages(appendix: Dict) -> List[int]:
    if appendix.get("appendix_kind") not in APPENDIX_PAGE_REVIEW_KINDS:
        return []
    physical_start = appendix.get("physical_start_page") or appendix.get("page")
    physical_end = appendix.get("physical_end_page") or physical_start
    if not physical_start or not physical_end or physical_end < physical_start:
        return []
    return list(range(int(physical_start), int(physical_end) + 1))


def dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    result: List[str] = []
    for item in items:
        normalized = str(item or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        result.append(normalized)
    return result


def enrich_appendix_markdown(
    document: Dict,
    appendices: List[Dict],
    source_pdf: Path,
    review_dir: Path,
    cache_path: Path | None = None,
    dpi: int = 220,
) -> tuple[List[Dict], Dict]:
    appendix_pages: Dict[str, List[int]] = {}
    needed_pages: List[int] = []

    for appendix in appendices:
        appendix["content_markdown"] = appendix.get("content") or ""
        appendix["content_source"] = "raw_text"
        appendix["content_review_required"] = False
        appendix["content_issues"] = []
        appendix["page_review_records"] = []

        pages = appendix_review_pages(appendix)
        if not pages:
            continue
        appendix_pages[appendix["id"]] = pages
        needed_pages.extend(pages)

    needed_pages = sorted(set(needed_pages))
    if not needed_pages:
        return appendices, {"provider_status": "not_needed", "processed_count": 0}

    page_results, cache_payload = review_pdf_pages_with_multimodal(
        document=document,
        pdf_path=source_pdf,
        pages=needed_pages,
        review_dir=review_dir,
        cache_path=cache_path,
        dpi=dpi,
    )

    for appendix in appendices:
        pages = appendix_pages.get(appendix["id"], [])
        if not pages:
            continue

        markdown_parts: List[str] = []
        issues: List[str] = []
        page_records: List[Dict] = []
        review_required = False

        for page_number in pages:
            result = page_results.get(page_number)
            if not result:
                review_required = True
                issues.append(f"第{page_number}页未生成附录复核结果。")
                continue

            page_records.append(
                {
                    "page": page_number,
                    "provider_status": result.get("provider_status"),
                    "review_required": bool(result.get("review_required")),
                    "issues": clean_issues_for_structure(result.get("issues", []) or []),
                    "page_markdown": result.get("page_markdown") or "",
                    "image_path": result.get("image_path"),
                }
            )
            review_required = review_required or bool(result.get("review_required"))
            issues.extend(f"第{page_number}页：{issue}" for issue in (result.get("issues") or []))
            if result.get("page_markdown"):
                markdown_parts.append(result["page_markdown"].strip())

        if markdown_parts:
            appendix["content_markdown"] = "\n\n".join(part for part in markdown_parts if part).strip()
            appendix["content"] = appendix["content_markdown"]
            appendix["content_source"] = "multimodal_page_review"
        appendix["content_review_required"] = review_required
        appendix["content_issues"] = clean_issues_for_structure(issues)
        appendix["page_review_records"] = page_records

    return appendices, cache_payload


def enrich_clauses(clauses: List[Dict], formula_review_pages: List[int]) -> List[Dict]:
    for clause in clauses:
        page_numbers = clause.get("page_numbers") or []
        review_pages = [page for page in formula_review_pages if page in page_numbers]
        text = clause.get("text", "")
        formula_sensitive = bool(review_pages) or looks_formula_sensitive_text(text)
        clause["start_page"] = clause.get("start_page") or (page_numbers[0] if page_numbers else None)
        clause["end_page"] = clause.get("end_page") or (page_numbers[-1] if page_numbers else None)
        clause["formula_review_pages"] = review_pages
        clause["formula_sensitive"] = formula_sensitive
        clause["review_priority"] = "high" if formula_sensitive else "normal"
        clause["default_markdown"] = strip_clause_prefix(
            text,
            clause.get("marker", ""),
            clause.get("label"),
        )
        clause["content_markdown"] = clause["default_markdown"]
        clause["content_source"] = "raw_text"
        clause["content_review_required"] = bool(formula_sensitive)
        clause["content_issues"] = (
            ["公式敏感条款仍为原生文本，尚未完成公式识别或人工回填。"]
            if formula_sensitive
            else []
        )
    return clauses


def initialize_appendix_delivery_fields(appendices: List[Dict]) -> List[Dict]:
    for appendix in appendices:
        appendix.setdefault("content_markdown", appendix.get("content") or "")
        appendix.setdefault("content_source", "raw_text")
        appendix.setdefault("page_review_records", [])
        unresolved_formula_appendix = bool(appendix.get("formula_review_pages")) or appendix.get(
            "appendix_kind"
        ) == "formula_model"
        if unresolved_formula_appendix and appendix.get("content_source") == "raw_text":
            appendix["content_review_required"] = True
            appendix["content_issues"] = dedupe_preserve_order(
                (appendix.get("content_issues") or [])
                + ["公式/模型附录仍为原生文本，尚未完成页面级识别或人工回填。"]
            )
        else:
            appendix.setdefault("content_review_required", False)
            appendix.setdefault("content_issues", [])
    return appendices


def build_page_table_appendices(pages: List[Dict]) -> Dict:
    """Represent tariff-only PDFs as page-level table attachments.

    Tariff tables contain many values such as ``1 千伏`` and ``35 千伏`` that
    resemble numeric section headings.  Treating them as rule clauses destroys
    the table/page boundary and produces false section nodes.  Page-level
    appendices preserve provenance while keeping these documents usable beside
    clause-based rules.
    """
    appendices: List[Dict] = []
    for page in pages:
        page_number = int(page["page"])
        content = "\n".join(line for line in page.get("lines", []) if line).strip()
        title = next(
            (
                line.replace(" ", "")
                for line in page.get("lines", [])
                if "电价表" in line and len(line) <= 80
            ),
            "输配电价表",
        )
        appendices.append(
            {
                "id": f"appendix-table-page-{page_number:03d}",
                "marker": f"第{page_number}页",
                "title": title,
                "page": page_number,
                "content": content,
                "start_page": page_number,
                "appendix_kind": "table",
                "logical_start_page": page_number,
                "physical_start_page": page_number,
                "physical_end_page": page_number,
                "formula_review_pages": [],
                "review_priority": "normal",
            }
        )
    return {"section_nodes": [], "clauses": [], "appendices": appendices}


def parse_body(pages: List[Dict], body_start_page: Optional[int]) -> Dict:
    section_nodes: List[Dict] = []
    clauses: List[Dict] = []
    appendices: List[Dict] = []

    current_chapter_id: Optional[str] = None
    current_section_id: Optional[str] = None
    current_appendix_id: Optional[str] = None
    current_clause: Optional[Dict] = None
    current_appendix_lines: List[str] = []
    current_appendix_start_page: Optional[int] = None

    chapter_count = 0
    section_count = 0
    appendix_count = 0
    clause_count = 0

    def flush_clause() -> None:
        nonlocal current_clause
        if not current_clause:
            return
        current_clause["text"] = compact_text(current_clause.pop("text_lines"))
        current_clause["end_page"] = current_clause["page_numbers"][-1]
        current_clause["referenced_appendices"] = sorted(
            {f"{prefix}{number}" for prefix, number in APPENDIX_REF_RE.findall(current_clause["text"])}
        )
        clauses.append(current_clause)
        current_clause = None

    def flush_appendix() -> None:
        nonlocal current_appendix_id, current_appendix_lines, current_appendix_start_page
        if not current_appendix_id:
            return
        appendix = next(item for item in appendices if item["id"] == current_appendix_id)
        appendix["content"] = compact_text(current_appendix_lines)
        appendix["start_page"] = current_appendix_start_page
        current_appendix_id = None
        current_appendix_lines = []
        current_appendix_start_page = None

    for page in pages:
        if body_start_page is not None and page["page"] < body_start_page:
            continue
        for line in merge_numeric_heading_lines(page["lines"]):
            appendix_match = APPENDIX_RE.match(line)
            chapter_match = CHAPTER_RE.match(line)
            section_match = SECTION_RE.match(line)
            clause_match = CLAUSE_RE.match(line)
            numeric_heading = parse_numeric_heading(line)

            if appendix_match:
                flush_clause()
                flush_appendix()
                appendix_count += 1
                marker = f"{appendix_match.group(1)}{appendix_match.group(2)}"
                title = appendix_match.group(3).strip()
                appendix_id = f"appendix-{appendix_count:02d}"
                node = {
                    "id": appendix_id,
                    "node_type": "appendix",
                    "marker": marker,
                    "title": title,
                    "page": page["page"],
                    "parent_id": None,
                }
                section_nodes.append(node)
                appendices.append(
                    {
                        "id": appendix_id,
                        "marker": marker,
                        "title": title,
                        "page": page["page"],
                        "content": "",
                    }
                )
                current_appendix_id = appendix_id
                current_appendix_start_page = page["page"]
                current_chapter_id = None
                current_section_id = None
                continue

            if chapter_match and not line.startswith("第十一条") and not line.startswith("第十二条"):
                flush_clause()
                chapter_count += 1
                chapter_id = f"chapter-{chapter_count:02d}"
                current_chapter_id = chapter_id
                current_section_id = None
                node = {
                    "id": chapter_id,
                    "node_type": "chapter",
                    "marker": chapter_match.group(1),
                    "title": chapter_match.group(2).strip(),
                    "page": page["page"],
                    "parent_id": None,
                }
                section_nodes.append(node)
                if current_appendix_id:
                    current_appendix_lines.append(line)
                continue

            if section_match:
                flush_clause()
                section_count += 1
                section_id = f"section-{section_count:02d}"
                current_section_id = section_id
                node = {
                    "id": section_id,
                    "node_type": "section",
                    "marker": section_match.group(1),
                    "title": section_match.group(2).strip(),
                    "page": page["page"],
                    "parent_id": current_chapter_id,
                }
                section_nodes.append(node)
                if current_appendix_id:
                    current_appendix_lines.append(line)
                continue

            if clause_match:
                flush_clause()
                clause_count += 1
                marker = clause_match.group(1)
                rest = clause_match.group(2).strip()
                label_match = CLAUSE_LABEL_RE.match(rest)
                clause_label = label_match.group(1) if label_match else None
                current_clause = {
                    "id": f"clause-{clause_count:03d}",
                    "marker": marker,
                    "label": clause_label,
                    "chapter_id": current_chapter_id,
                    "section_id": current_section_id,
                    "appendix_id": current_appendix_id,
                    "start_page": page["page"],
                    "page_numbers": [page["page"]],
                    "text_lines": [f"{marker} {rest}".strip()],
                }
                continue

            if numeric_heading and not current_appendix_id:
                flush_clause()
                marker, title = numeric_heading
                section_count += 1
                section_id = f"section-{section_count:02d}"
                current_section_id = section_id
                node = {
                    "id": section_id,
                    "node_type": "section",
                    "marker": marker,
                    "title": title,
                    "page": page["page"],
                    "parent_id": current_chapter_id,
                }
                section_nodes.append(node)
                clause_count += 1
                current_clause = {
                    "id": f"clause-{clause_count:03d}",
                    "marker": marker,
                    "label": title,
                    "chapter_id": current_chapter_id,
                    "section_id": current_section_id,
                    "appendix_id": None,
                    "start_page": page["page"],
                    "page_numbers": [page["page"]],
                    "text_lines": [f"{marker} {title}"],
                }
                continue

            if current_clause:
                if page["page"] not in current_clause["page_numbers"]:
                    current_clause["page_numbers"].append(page["page"])
                current_clause["text_lines"].append(line)
            elif current_appendix_id:
                current_appendix_lines.append(line)

    flush_clause()
    flush_appendix()

    return {
        "section_nodes": section_nodes,
        "clauses": clauses,
        "appendices": appendices,
    }


def build_markdown(structured: Dict, include_review_notes: bool = False) -> str:
    doc = structured["document"]
    counts = structured["structure_summary"]
    quality = structured["quality_summary"]
    lines: List[str] = []

    lines.append(f"# {doc['title']}")
    lines.append("")
    lines.append("## 结构摘要")
    lines.append(f"- 版本标识：`{doc['version_label']}`")
    lines.append(f"- 源文件：`{doc['source_file_name']}`")
    lines.append(f"- 物理页数：`{doc['total_physical_pages']}`")
    lines.append(f"- 逻辑起始页：`{doc['logical_start_page']}`")
    lines.append(f"- 目录起始页：`{doc['toc_start_page']}`")
    lines.append(f"- 正文起始页：`{doc['body_start_page']}`")
    lines.append(f"- 附录起始页：`{doc['appendix_start_page']}`")
    lines.append(f"- 章节数：`{counts['chapter_count']}`")
    lines.append(f"- 节数：`{counts['section_count']}`")
    lines.append(f"- 条款数：`{counts['clause_count']}`")
    lines.append(f"- 附录数：`{counts['appendix_count']}`")
    lines.append("")
    lines.append("## 质量摘要")
    lines.append(f"- 推荐流程：`{quality['recommended_pipeline']}`")
    lines.append(f"- OCR 复核页：`{', '.join(map(str, quality['ocr_review_pages'])) if quality['ocr_review_pages'] else '无'}`")
    lines.append(f"- 公式复核页：`{', '.join(map(str, quality['formula_review_pages'])) if quality['formula_review_pages'] else '无'}`")
    lines.append("")

    if structured["toc_entries"]:
        lines.append("## 目录")
        for entry in structured["toc_entries"]:
            lines.append(
                f"- `{entry['marker']}` {entry['title']} -> 目录页码 `{entry['target_page']}`"
            )
        lines.append("")

    lines.append("## 正文条款")
    section_node_by_id = {item["id"]: item for item in structured["section_nodes"]}
    seen_section_headers: set[str] = set()
    for clause in structured["clauses"]:
        chapter = section_node_by_id.get(clause["chapter_id"]) if clause["chapter_id"] else None
        section = section_node_by_id.get(clause["section_id"]) if clause["section_id"] else None
        if chapter and chapter["id"] not in seen_section_headers:
            lines.append(f"### {chapter['marker']} {chapter['title']}")
            lines.append("")
            seen_section_headers.add(chapter["id"])
        if section and section["id"] not in seen_section_headers:
            lines.append(f"#### {section['marker']} {section['title']}")
            lines.append("")
            seen_section_headers.add(section["id"])
        suffix = f" [{clause['label']}]" if clause["label"] else ""
        lines.append(f"##### {clause['marker']}{suffix}")
        if clause["referenced_appendices"]:
            lines.append(f"- 引用附录：`{', '.join(clause['referenced_appendices'])}`")
        if include_review_notes and clause.get("formula_sensitive"):
            lines.append("- 复核提示：`该条款含公式或复杂计算表达，参数提取与展示需谨慎。`")
        if include_review_notes and clause.get("content_source") == "multimodal_formula":
            lines.append("- 内容来源：`多模态公式识别回填`")
        if include_review_notes and clause.get("content_review_required"):
            lines.append("- 复核状态：`该条款仍建议人工核对公式识别结果。`")
        if include_review_notes and clause.get("content_issues"):
            for issue in clause["content_issues"]:
                lines.append(f"- 识别备注：`{clean_issue_for_markdown(issue)}`")
        lines.append("")
        lines.append(clause.get("content_markdown") or clause["text"])
        lines.append("")

    if structured["appendices"]:
        lines.append("## 附录")
        for appendix in structured["appendices"]:
            lines.append(f"### {appendix['marker']} {appendix['title']}")
            lines.append(f"- 类型：`{appendix['appendix_kind']}`")
            lines.append(f"- 逻辑起始页：`{appendix['logical_start_page']}`")
            lines.append(f"- 物理页范围：`{appendix['physical_start_page']}-{appendix['physical_end_page']}`")
            lines.append(f"- 复核优先级：`{appendix['review_priority']}`")
            if include_review_notes and appendix.get("content_source") == "multimodal_page_review":
                lines.append("- 内容来源：`多模态页面复核回填`")
            if include_review_notes and appendix.get("content_review_required"):
                lines.append("- 复核状态：`附录页面仍建议人工核对。`")
            if include_review_notes and appendix["formula_review_pages"]:
                lines.append(f"- 公式复核页：`{', '.join(map(str, appendix['formula_review_pages']))}`")
            if include_review_notes and appendix.get("content_issues"):
                for issue in appendix["content_issues"][:4]:
                    lines.append(f"- 识别备注：`{clean_issue_for_markdown(issue)}`")
            lines.append("")
            lines.append(appendix.get("content_markdown") or appendix["content"] or "_附录内容待补_")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def normalize_delivery_fields(structured: Dict) -> None:
    """Keep final JSON mirrors aligned with reviewed Markdown content."""
    for clause in structured.get("clauses", []):
        content_markdown = clause.get("content_markdown")
        if content_markdown:
            clause["text"] = content_markdown
            clause["default_markdown"] = content_markdown
        clause.pop("backfill_notes", None)
    for appendix in structured.get("appendices", []):
        content_markdown = appendix.get("content_markdown")
        if content_markdown:
            appendix["content"] = content_markdown
        appendix.pop("backfill_notes", None)


def build_structure(args: argparse.Namespace) -> int:
    raw_text_path = resolve_path(args.raw_text)
    report_path = resolve_path(args.report_json)
    output_json = resolve_path(args.output_json)
    output_md = resolve_path(args.output_md)
    source_pdf = resolve_path(args.source_pdf)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)

    pages = load_pages(raw_text_path)
    markers = detect_document_markers(pages)
    toc_entries = parse_toc_entries(
        pages, markers["toc_start_page"], markers["body_start_page"]
    )
    parsed = (
        build_page_table_appendices(pages)
        if args.rule_type in TABULAR_RULE_TYPES
        else parse_body(pages, markers["body_start_page"])
    )
    quality_report = json.loads(report_path.read_text(encoding="utf-8"))
    parsed["clauses"] = enrich_clauses(
        parsed["clauses"],
        quality_report["pages_requiring_formula_review"],
    )
    if args.rule_type not in TABULAR_RULE_TYPES:
        parsed["appendices"] = enrich_appendices(
            parsed["appendices"],
            toc_entries,
            pages,
            max((page["page"] for page in pages), default=0),
            markers["body_start_page"],
            quality_report["pages_requiring_formula_review"],
        )
    parsed["appendices"] = initialize_appendix_delivery_fields(parsed["appendices"])

    if args.enable_formula_markdown:
        report_stem = report_path.stem.replace("_report", "")
        formula_review_dir = resolve_path(args.formula_review_dir) if args.formula_review_dir else raw_text_path.parent / f"{report_stem}_formula_review"
        formula_cache = resolve_path(args.formula_cache_json) if args.formula_cache_json else raw_text_path.parent / f"{report_stem}_formula_mm_cache.json"
        parsed["clauses"], formula_cache_payload = apply_formula_markdown(
            {"title": extract_title(pages, markers["title_page"], source_pdf.name), "rule_type": args.rule_type, "version_label": args.version_label},
            parsed["clauses"],
            source_pdf,
            formula_review_dir,
            formula_cache,
            dpi=args.formula_dpi,
        )
    else:
        formula_review_dir = None
        formula_cache = None
        formula_cache_payload = {"provider_status": "disabled"}

    if args.enable_appendix_markdown:
        report_stem = report_path.stem.replace("_report", "")
        appendix_review_dir = resolve_path(args.appendix_review_dir) if args.appendix_review_dir else raw_text_path.parent / f"{report_stem}_appendix_review"
        appendix_cache = resolve_path(args.appendix_cache_json) if args.appendix_cache_json else raw_text_path.parent / f"{report_stem}_appendix_mm_cache.json"
        parsed["appendices"], appendix_cache_payload = enrich_appendix_markdown(
            {
                "title": extract_title(pages, markers["title_page"], source_pdf.name),
                "rule_type": args.rule_type,
                "version_label": args.version_label,
            },
            parsed["appendices"],
            source_pdf,
            appendix_review_dir,
            appendix_cache,
            dpi=args.appendix_dpi,
        )
    else:
        appendix_review_dir = None
        appendix_cache = None
        appendix_cache_payload = {"provider_status": "disabled"}

    document_title = extract_title(pages, markers["title_page"], source_pdf.name)
    structured = {
        "document": {
            "id": args.document_id,
            "title": document_title,
            "version_label": args.version_label,
            "rule_type": args.rule_type,
            "source_path": str(source_pdf),
            "source_file_name": source_pdf.name,
            "raw_text_path": str(raw_text_path),
            "report_json_path": str(report_path),
            "total_physical_pages": max((page["page"] for page in pages), default=0),
            "logical_start_page": markers["title_page"],
            "toc_start_page": markers["toc_start_page"],
            "body_start_page": markers["body_start_page"],
            "appendix_start_page": markers["appendix_start_page"],
            "pre_body_pages": [
                page["page"]
                for page in pages
                if markers["body_start_page"] and page["page"] < markers["body_start_page"]
            ],
        },
        "toc_entries": toc_entries,
        "section_nodes": parsed["section_nodes"],
        "clauses": parsed["clauses"],
        "appendices": parsed["appendices"],
        "quality_summary": quality_report["document_strategy"],
        "page_quality_overview": {
            "ocr_review_pages": quality_report["pages_requiring_ocr_review"],
            "formula_review_pages": quality_report["pages_requiring_formula_review"],
        },
        "formula_processing": {
            "enabled": bool(args.enable_formula_markdown),
            "review_dir": str(formula_review_dir) if formula_review_dir else None,
            "cache_path": str(formula_cache) if formula_cache else None,
            "provider_status": formula_cache_payload.get("provider_status"),
            "processed_count": formula_cache_payload.get("processed_count", 0),
            "cache_hit_count": formula_cache_payload.get("cache_hit_count", 0),
            "cache_miss_count": formula_cache_payload.get("cache_miss_count", 0),
            "reason": formula_cache_payload.get("reason"),
        },
        "appendix_processing": {
            "enabled": bool(args.enable_appendix_markdown),
            "review_dir": str(appendix_review_dir) if appendix_review_dir else None,
            "cache_path": str(appendix_cache) if appendix_cache else None,
            "provider_status": appendix_cache_payload.get("provider_status"),
            "processed_count": appendix_cache_payload.get("processed_count", 0),
            "cache_hit_count": appendix_cache_payload.get("cache_hit_count", 0),
            "cache_miss_count": appendix_cache_payload.get("cache_miss_count", 0),
            "reason": appendix_cache_payload.get("reason"),
        },
        "structure_summary": {
            "chapter_count": sum(
                1 for item in parsed["section_nodes"] if item["node_type"] == "chapter"
            ),
            "section_count": sum(
                1 for item in parsed["section_nodes"] if item["node_type"] == "section"
            ),
            "appendix_count": len(parsed["appendices"]),
            "clause_count": len(parsed["clauses"]),
        },
    }

    normalize_delivery_fields(structured)

    output_json.write_text(
        json.dumps(structured, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    output_md.write_text(build_markdown(structured, include_review_notes=args.include_review_notes), encoding="utf-8")

    print(f"Resolved raw text: {raw_text_path}")
    print(f"Resolved report: {report_path}")
    print(f"Resolved source PDF: {source_pdf}")
    print(f"JSON written: {output_json}")
    print(f"Markdown written: {output_md}")
    print(
        "Summary: "
        f"chapters={structured['structure_summary']['chapter_count']}, "
        f"sections={structured['structure_summary']['section_count']}, "
        f"clauses={structured['structure_summary']['clause_count']}, "
        f"appendices={structured['structure_summary']['appendix_count']}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build first-pass rule structure artifacts")
    parser.add_argument("--raw-text", required=True, help="Extracted raw text file")
    parser.add_argument("--report-json", required=True, help="Page quality report JSON")
    parser.add_argument("--source-pdf", required=True, help="Source PDF path")
    parser.add_argument("--document-id", required=True, help="Structured document id")
    parser.add_argument("--version-label", required=True, help="Version label, e.g. 2025")
    parser.add_argument("--rule-type", default="spot", help="Rule type label")
    parser.add_argument("--output-json", required=True, help="Output JSON path")
    parser.add_argument("--output-md", required=True, help="Output Markdown path")
    parser.add_argument(
        "--include-review-notes",
        action="store_true",
        help="Include review status and OCR/formula notes in Markdown. Leave disabled for reusable delivery Markdown.",
    )
    parser.add_argument(
        "--enable-formula-markdown",
        action="store_true",
        help="Use multimodal formula recognition to rewrite formula-sensitive clauses into Markdown with LaTeX",
    )
    parser.add_argument(
        "--formula-review-dir",
        help="Directory for rendered formula review images; defaults to tmp/pdfs/<report_stem>_formula_review",
    )
    parser.add_argument(
        "--formula-cache-json",
        help="Optional cache JSON for multimodal formula results; defaults to tmp/pdfs/<report_stem>_formula_mm_cache.json",
    )
    parser.add_argument(
        "--formula-dpi",
        type=int,
        default=220,
        help="Render DPI for formula review images",
    )
    parser.add_argument(
        "--enable-appendix-markdown",
        action="store_true",
        help="Use multimodal page review to rewrite parameter/model appendices into Markdown",
    )
    parser.add_argument(
        "--appendix-review-dir",
        help="Directory for rendered appendix review images; defaults to tmp/pdfs/<report_stem>_appendix_review",
    )
    parser.add_argument(
        "--appendix-cache-json",
        help="Optional cache JSON for appendix page multimodal results; defaults to tmp/pdfs/<report_stem>_appendix_mm_cache.json",
    )
    parser.add_argument(
        "--appendix-dpi",
        type=int,
        default=220,
        help="Render DPI for appendix page review images",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return build_structure(args)


if __name__ == "__main__":
    raise SystemExit(main())
