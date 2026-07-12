#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build parameter-oriented catalogs from structured rule JSON and compare versions.

This script intentionally complements `build_rule_structure.py`:
1. rule structure JSON keeps the document as a stable text carrier
2. parameter catalog JSON rewrites numeric rules into comparison-oriented objects

Supported workflow:
  python build_parameter_catalog.py build --input ... --output ...
  python build_parameter_catalog.py compare --old ... --new ... --output-json ... --output-md ...
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


APPENDIX_TARGETS = {
    "附录3",
    "附录4",
    "附录5",
    "附录三",
    "附录四",
    "附录五",
    "附件3",
    "附件4",
    "附件5",
    "附件三",
    "附件四",
    "附件五",
}
TABLE_HEADER_RE = re.compile(r"序号\s*参数名称\s*取值")
TABLE_HEADER_HINT_RE = re.compile(r"(序号\s*参数名称\s*取值|阶段\s*标的时间\s*置换出上限)")
CHINESE_ENUM_RE = re.compile(r"（[一二三四五六七八九十]+）")
ROW_INDEX_RE = re.compile(r"(?<!\d)(?P<idx>\d{1,2})\s+(?=[\u4e00-\u9fffA-Za-z（(])")
TIME_POINT_RE = re.compile(r"(?P<value>\d{1,2}:\d{2})")
STARTUP_FEE_BAND_RE = re.compile(
    r"机组额定容量级别在\s*(?P<band>\d+\s*MW(?:\s*及以下|\s*及以上|\s*以上)?(?:\s*至\s*\d+\s*MW)?)\s*时，\s*"
    r"冷态启动上限为\s*(?P<cold>\d+\s*万元/\s*次)\s*、\s*"
    r"温态启动上限为\s*(?P<warm>\d+\s*万元/\s*次)\s*、\s*"
    r"热态启动上限为\s*(?P<hot>\d+\s*万元/\s*次)"
)
RANGE_RE = re.compile(
    r"(?P<first>-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*"
    r"(?P<unit1>元/MWh|万元/次|MW/分钟|MW|MWh|kV|千伏|分钟|小时|次|%)?"
    r"\s*(?P<connector>-|~|～|至)\s*"
    r"(?P<second>-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*"
    r"(?P<unit2>元/MWh|万元/次|MW/分钟|MW|MWh|kV|千伏|分钟|小时|次|%)"
)
SINGLE_VALUE_RE = re.compile(
    r"(?P<value>-?\d+(?:\.\d+)?(?:e[+-]?\d+)?)\s*"
    r"(?P<unit>元/MWh|万元/次|MW/分钟|MW|MWh|kV|千伏|分钟|小时|次|%|个时段|个出力段|个点|个)?"
)
UNIT_HINT_RE = re.compile(r"单位为\s*(元/MWh|万元/次|MW/分钟|MW|MWh|kV|千伏|分钟|小时|次|%)")
NOISE_BLOCK_RE = re.compile(r"\{\s*,\s*\d+[^{}]{0,40}?榰")
SUBJECT_RE = re.compile(
    r"(火电机组|火电企业|火电|新能源场站|新能源企业|新能源|独立新型储能电站|独立储能电站|独立新型储能设施|独立储能设施|储能电站|储能设施|储能|"
    r"SCUC或SCED|SCUC|SCED|节点电价计算模型|节点价格计算|节点电价|充电|放电|报量报价|报量不报价|"
    r"\d+\s*MW\s*(?:及以下|以上)|\d+\s*MW\s*至\s*\d+\s*MW|\d+(?:\.\d+)?%\s*-\s*\d+(?:\.\d+)?%|\d+(?:\.\d+)?%\s*~\s*\d+(?:\.\d+)?%)"
)

CLAUSE_TRIGGER_KEYWORDS = (
    "上限",
    "下限",
    "限值",
    "罚因子",
    "惩罚因子",
    "系数",
    "比例",
    "时长",
    "时间间隔",
    "次数",
    "分钟",
    "小时",
    "时段",
    "电价",
    "价格",
    "报价",
    "出力",
    "功率",
    "容量",
    "负荷",
    "kV",
    "千伏",
    "MW",
    "MWh",
    "控制裕度",
)

ROLE_KEYWORDS = (
    "价格下限",
    "价格上限",
    "出清价格下限",
    "出清价格上限",
    "申报价格下限",
    "申报价格上限",
    "下限",
    "上限",
    "限值",
    "罚因子",
    "惩罚因子",
    "系数",
    "次数上限",
    "次数",
    "时长",
    "时间间隔",
    "控制裕度",
    "荷电状态",
    "功率",
    "容量",
    "电压",
    "报价",
)

STOP_PREFIXES = ("第", "附录", "附件", "D-", "T-", "20")
FORMULA_CONTEXT_RE = re.compile(r"(计算公式|具体公式|公式如下|公式为|分摊返还方式|求和|返还方式)")
FORMULA_SYMBOL_RE = re.compile(r"[=+\-*/%<>∑ΣΠπΔλβμ±÷×]")
SINGLE_LETTER_TOKEN_RE = re.compile(r"(?<![A-Za-z])[A-Za-z](?![A-Za-z])")
LATEX_BLOCK_RE = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
TABLE_SEPARATOR_LINE_RE = re.compile(
    r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$",
    re.MULTILINE,
)
ROW_ITEM_RE = re.compile(r"(?:第(?P<item>\d+)项|序号(?P<row>\d+))")


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def normalize_text(text: str) -> str:
    text = NOISE_BLOCK_RE.sub(" ", text)
    text = TABLE_HEADER_RE.sub(" ", text)
    text = text.replace("\x00", " ")
    text = text.replace("\u0098", " ")
    text = text.replace("（ D", "（D")
    text = re.sub(r"(?<![\d.])(\d{1,2})时\s*(\d{1,2})\s*分", r"\1:\2", text)
    text = re.sub(
        r"(?<![\d.])(\d{1,2})时(?=\s*(前|后|至|止|，|。|；|$))",
        r"\1:00",
        text,
    )
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[（《“])\s+", "", text)
    text = re.sub(r"\s+(?=[）》”])", "", text)
    text = re.sub(r"\s+([,.;:])", r"\1", text)
    return text.strip()


def markdown_to_plain_text(text: str) -> str:
    if not text:
        return ""
    cleaned = LATEX_BLOCK_RE.sub(" 公式块 ", text)
    cleaned = cleaned.replace("$$", " ")
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"^#+\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = TABLE_SEPARATOR_LINE_RE.sub(" ", cleaned)
    cleaned = cleaned.replace("|", " ")
    cleaned = cleaned.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"\n{2,}", "。", cleaned)
    cleaned = cleaned.replace("\n", " ")
    return normalize_text(cleaned)


def normalize_key_text(text: str) -> str:
    text = normalize_text(text)
    text = re.sub(r"[，。；：、（）()《》“”\"'`·\s]+", "", text)
    return text.lower()


def formula_token_score(text: str) -> int:
    if not text:
        return 0
    private_use_chars = sum(1 for ch in text if 0xE000 <= ord(ch) <= 0xF8FF)
    math_symbols = len(FORMULA_SYMBOL_RE.findall(text))
    single_letters = len(SINGLE_LETTER_TOKEN_RE.findall(text))
    return private_use_chars * 4 + math_symbols + single_letters


def looks_formula_sensitive_text(text: str) -> bool:
    if not text:
        return False
    compact = normalize_text(text)
    score = formula_token_score(compact)
    if FORMULA_CONTEXT_RE.search(compact) and score >= 6:
        return True
    if score >= 18:
        return True
    if "）（）（" in compact or "" in compact or "" in compact:
        return True
    return False


def safe_statement_preview(statement: str) -> str:
    if looks_formula_sensitive_text(statement):
        return "该处涉及复杂公式或计算表达，已不作为前端参数证据直接展示。"
    return statement


def should_skip_statement(statement: str) -> bool:
    return looks_formula_sensitive_text(statement)


def split_statements(text: str) -> List[str]:
    parts = re.split(r"[。；;]", text)
    return [part.strip(" ，、") for part in parts if part.strip(" ，、")]


def dedupe_repeated_prefix(text: str) -> str:
    for size in range(2, 13):
        prefix = text[:size]
        if prefix and text.startswith(prefix * 2):
            return text[size:]
    return text


def dedupe_repeated_suffix(text: str) -> str:
    for size in range(2, min(12, len(text) // 2) + 1):
        suffix = text[-size:]
        if suffix and text.endswith(suffix * 2):
            return text[:-size]
    return text


def normalize_segment_name_text(text: str) -> str:
    cleaned = dedupe_repeated_prefix(normalize_text(text))
    cleaned = dedupe_repeated_suffix(cleaned)
    return cleaned.strip(" ：，、")


def infer_name_from_text(text: str, fallback: str) -> str:
    text = dedupe_repeated_prefix(text.strip())
    for cue in ("单位为", "是指", "暂定为", "取", "包括", "应在", "按照", "当满足", "用于", "代表", "指"):
        index = text.find(cue)
        if 1 <= index <= 40:
            return text[:index].strip(" ：，、")
    punctuation = re.search(r"[：，。； ]", text)
    if punctuation and 1 <= punctuation.start() <= 36:
        return text[: punctuation.start()].strip(" ：，、")
    return fallback


def detect_parameter_category(label: str, unit: str, value_type: str) -> str:
    unit = unit or ""
    if "罚因子" in label or "惩罚因子" in label:
        return "penalty_factor"
    if "价格" in label and any(token in label for token in ("上限", "下限", "限值")):
        return "price_limit"
    if "时间" in label or value_type == "time_point":
        return "time_point"
    if "时长" in label or "分钟" in unit or "小时" in unit:
        return "duration"
    if "次数" in label or unit == "次":
        return "count_limit"
    if unit == "%" or "%" in label or value_type == "range_percent":
        return "ratio_threshold"
    if "电压" in label or unit in {"kV", "千伏"}:
        return "voltage_level"
    if unit in {"MW", "MW/分钟", "MWh"} or any(token in label for token in ("功率", "容量", "出力", "荷电状态")):
        return "power_capacity"
    return "generic_numeric_rule"


def is_parameter_clause(text: str) -> bool:
    if not re.search(r"\d", text):
        return False
    return any(keyword in text for keyword in CLAUSE_TRIGGER_KEYWORDS)


def looks_like_parameter_appendix(appendix: Dict) -> bool:
    if appendix["marker"] in APPENDIX_TARGETS:
        return True
    if appendix.get("appendix_kind") == "parameter":
        return True
    text = appendix_source_text(appendix)
    if not text:
        return False
    if TABLE_HEADER_HINT_RE.search(text):
        return True
    if "参数" in (appendix.get("title") or "") and "取值" in text:
        return True
    return False


def appendix_source_text(appendix: Dict) -> str:
    reviewed_markdown = appendix.get("content_markdown")
    if reviewed_markdown:
        return markdown_to_plain_text(reviewed_markdown)
    return normalize_text(appendix.get("content") or "")


def appendix_source_formula_sensitive(appendix: Dict) -> bool:
    if appendix.get("appendix_kind") == "formula_model":
        return True
    if appendix.get("content_review_required"):
        return True
    if appendix.get("content_source") == "multimodal_page_review" and appendix.get(
        "content_markdown"
    ):
        return False
    return bool(appendix.get("formula_review_pages"))


def normalize_scope_name(scope_name: str) -> str:
    scope = normalize_text(scope_name or "")
    scope = re.sub(r"^(?:附录|附件)\s*[0-9一二三四五六七八九十]+\s*", "", scope)
    return scope.strip(" ：，、")


def build_appendix_comparison_subject(
    appendix_title: str,
    scope_name: str,
    row_name: str,
) -> str:
    appendix_scope = normalize_scope_name(appendix_title)
    scope = normalize_scope_name(scope_name)
    row = normalize_segment_name_text(row_name)
    generic_scopes = {"", appendix_scope, "默认申报参数", "市场核定参数", "机组运行参数"}
    if scope not in generic_scopes:
        return f"{scope}-{row}"
    return row


def markdown_table_cells(line: str) -> List[str]:
    stripped = line.strip()
    if not stripped or "|" not in stripped:
        return []
    stripped = stripped.strip("|")
    return [normalize_text(cell) for cell in stripped.split("|")]


def is_markdown_table_separator(line: str) -> bool:
    compact = line.strip()
    if not compact:
        return False
    return bool(TABLE_SEPARATOR_LINE_RE.match(compact))


def build_markdown_table_segments(
    appendix: Dict,
    start_index: int,
) -> Tuple[List[Dict], int]:
    page_records = appendix.get("page_review_records") or []
    if any(record.get("page_markdown") for record in page_records):
        segments: List[Dict] = []
        next_index = start_index
        for record in page_records:
            page_markdown = record.get("page_markdown") or ""
            if "|" not in page_markdown:
                continue
            scoped_segments, next_index = parse_markdown_table_segments(
                appendix=appendix,
                markdown_text=page_markdown,
                start_index=next_index,
                source_formula_sensitive=bool(record.get("review_required")),
                review_issues=record.get("issues") or [],
                source_suffix=f" / 第{record.get('page')}页" if record.get("page") else "",
            )
            segments.extend(scoped_segments)
        if segments:
            return segments, next_index

    markdown_text = appendix.get("content_markdown") or ""
    if "|" not in markdown_text:
        return [], start_index
    return parse_markdown_table_segments(
        appendix=appendix,
        markdown_text=markdown_text,
        start_index=start_index,
        source_formula_sensitive=appendix_source_formula_sensitive(appendix),
        review_issues=appendix.get("content_issues") or [],
        source_suffix="",
    )


def page_wide_review_required(issues: Sequence[str]) -> bool:
    meaningful = [normalize_text(issue) for issue in issues if normalize_text(issue)]
    if not meaningful:
        return False
    for issue in meaningful:
        if "物理页码" in issue or "PDF阅读器页码" in issue or "页码" in issue:
            continue
        if ROW_ITEM_RE.search(issue):
            continue
        return True
    return False


def review_affected_row_indexes(issues: Sequence[str]) -> set[int]:
    affected: set[int] = set()
    for issue in issues:
        normalized = normalize_text(issue)
        if not normalized:
            continue
        for match in ROW_ITEM_RE.finditer(normalized):
            row_text = match.group("row") or match.group("item")
            if not row_text:
                continue
            row_index = int(row_text)
            affected.add(row_index)
            if "之前" in normalized and row_index > 1:
                affected.add(row_index - 1)
    return affected


def parse_markdown_table_segments(
    appendix: Dict,
    markdown_text: str,
    start_index: int,
    source_formula_sensitive: bool,
    review_issues: Sequence[str],
    source_suffix: str,
) -> Tuple[List[Dict], int]:
    segments: List[Dict] = []
    next_index = start_index
    current_scope = appendix.get("title") or appendix.get("marker")
    table_active = False
    table_mode = ""
    implicit_row_index = 0
    page_wide_block = page_wide_review_required(review_issues)
    affected_rows = review_affected_row_indexes(review_issues)

    for raw_line in markdown_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        heading_match = re.match(r"^#{1,6}\s*(.+?)\s*$", line)
        if heading_match:
            current_scope = heading_match.group(1).strip()
            table_active = False
            table_mode = ""
            continue

        if is_markdown_table_separator(line):
            continue

        cells = markdown_table_cells(line)
        if len(cells) < 3:
            table_active = False
            table_mode = ""
            continue

        if "序号" in cells[0] and "参数" in cells[1] and "取值" in cells[2]:
            table_active = True
            table_mode = "indexed"
            implicit_row_index = 0
            continue

        if "参数" in cells[0] and ("含义" in cells[1] or "参数名称" in cells[1]) and "取值" in cells[2]:
            table_active = True
            table_mode = "parameter_meaning_value"
            implicit_row_index = 0
            continue

        if not table_active:
            continue

        if table_mode == "indexed":
            row_index_text = re.sub(r"\s+", "", cells[0])
            if not row_index_text.isdigit():
                continue

            row_index = int(row_index_text)
            if row_index > 30:
                continue

            row_name = normalize_segment_name_text(cells[1])
            row_value = normalize_text(" ".join(cells[2:]))
            source_item_label = f"序号{row_index} {row_name}"
            statement_text = normalize_text(f"{row_name}：{row_value}")
        else:
            implicit_row_index += 1
            row_index = implicit_row_index
            row_symbol = normalize_text(cells[0])
            row_name = normalize_segment_name_text(cells[1])
            row_value = normalize_text(" ".join(cells[2:]))
            source_item_label = f"{row_symbol} {row_name}"
            statement_text = normalize_text(f"{row_symbol} {row_name}：{row_value}")

        if not row_name or not row_value:
            continue

        comparison_subject = build_appendix_comparison_subject(
            appendix.get("title", ""),
            current_scope,
            row_name,
        )

        row_formula_sensitive = source_formula_sensitive and (
            page_wide_block or row_index in affected_rows or not affected_rows
        )

        segments.append(
            {
                "id": f"segment-{next_index:03d}",
                "source_type": "appendix",
                "source_marker": appendix["marker"],
                "source_label": appendix["title"],
                "source_item_marker": None,
                "source_item_index": row_index,
                "segment_name": comparison_subject,
                "comparison_subject": comparison_subject,
                "statement_text": statement_text,
                "display_statement_text": safe_statement_preview(statement_text),
                "source_ref": f"{appendix['marker']} {appendix['title']} / {source_item_label}{source_suffix}",
                "source_quality": appendix.get("review_priority", "normal"),
                "source_formula_sensitive": row_formula_sensitive,
                "source_table_like": False,
            }
        )
        next_index += 1

    return segments, next_index


def is_table_like_statement(statement: str) -> bool:
    compact = normalize_text(statement)
    if not compact:
        return False
    if TABLE_HEADER_HINT_RE.search(compact):
        return True
    row_matches = [match for match in ROW_INDEX_RE.finditer(compact) if int(match.group("idx")) <= 30]
    dense_numeric_count = len(
        re.findall(r"\d+(?:\.\d+)?\s*(?:小时|分钟|%|MW|MWh|次)", compact)
    )
    if len(row_matches) >= 3 and dense_numeric_count >= 3:
        return True
    if "占持有合约比例" in compact and "阶段" in compact:
        return True
    return False


def build_appendix3_segments(appendix: Dict, start_index: int) -> Tuple[List[Dict], int]:
    text = appendix_source_text(appendix)
    sections = re.split(r"(常规机组运行参数|独立新型储能电站运行参数)", text)
    segments: List[Dict] = []
    next_index = start_index

    if len(sections) < 3:
        return build_enumerated_segments(
            appendix, text, "常规机组运行参数", start_index
        )

    for idx in range(1, len(sections), 2):
        scope = sections[idx].strip()
        body = sections[idx + 1].strip() if idx + 1 < len(sections) else ""
        scoped_segments, next_index = build_enumerated_segments(
            appendix, body, scope, next_index
        )
        segments.extend(scoped_segments)

    return segments, next_index


def build_enumerated_segments(
    appendix: Dict,
    text: str,
    scope_name: str,
    start_index: int,
) -> Tuple[List[Dict], int]:
    matches = list(CHINESE_ENUM_RE.finditer(text))
    if not matches:
        return [], start_index

    segments: List[Dict] = []
    next_index = start_index
    for idx, match in enumerate(matches):
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        block = normalize_text(text[match.start() : end])
        block = dedupe_repeated_prefix(block)
        entry_name = infer_name_from_text(block, f"{scope_name}-{match.group(0)}")
        comparison_subject = f"{scope_name}-{entry_name}"
        segments.append(
            {
                "id": f"segment-{next_index:03d}",
                "source_type": "appendix",
                "source_marker": appendix["marker"],
                "source_label": appendix["title"],
                "source_item_marker": match.group(0),
                "source_item_index": None,
                "segment_name": comparison_subject,
                "comparison_subject": comparison_subject,
                "statement_text": block,
                "display_statement_text": safe_statement_preview(block),
                "source_ref": f"{appendix['marker']} {appendix['title']} / {match.group(0)} {entry_name}",
                "source_quality": appendix.get("review_priority", "normal"),
                "source_formula_sensitive": appendix_source_formula_sensitive(appendix),
            }
        )
        next_index += 1
    return segments, next_index


def build_table_segments(appendix: Dict, start_index: int) -> Tuple[List[Dict], int]:
    markdown_segments, next_index = build_markdown_table_segments(appendix, start_index)
    if markdown_segments:
        return markdown_segments, next_index

    text = appendix_source_text(appendix)
    segments: List[Dict] = []
    next_index = start_index
    headers = [
        "常规机组默认申报参数",
        "独立新型储能电站默认申报参数",
    ]
    section_parts = re.split(
        r"(常规机组默认申报参数|独立新型储能电站默认申报参数)",
        text,
    )

    if len(section_parts) >= 3:
        for idx in range(1, len(section_parts), 2):
            scope_name = section_parts[idx].strip()
            body = section_parts[idx + 1].strip() if idx + 1 < len(section_parts) else ""
            scoped_segments, next_index = build_table_rows(
                appendix, body, scope_name, next_index
            )
            segments.extend(scoped_segments)
        return segments, next_index

    if any(header in text for header in headers):
        text = text

    scoped_segments, next_index = build_table_rows(
        appendix, text, appendix["title"], next_index
    )
    segments.extend(scoped_segments)

    return segments, next_index


def build_table_rows(
    appendix: Dict,
    text: str,
    scope_name: str,
    start_index: int,
) -> Tuple[List[Dict], int]:
    matches = [match for match in ROW_INDEX_RE.finditer(text) if int(match.group("idx")) <= 30]
    selected: List[re.Match[str]] = []
    expected = 1
    for match in matches:
        idx = int(match.group("idx"))
        if not selected and idx != 1:
            continue
        if not selected or idx == expected or idx == int(selected[-1].group("idx")) + 1:
            selected.append(match)
            expected = idx + 1

    segments: List[Dict] = []
    next_index = start_index
    for idx, match in enumerate(selected):
        end = selected[idx + 1].start() if idx + 1 < len(selected) else len(text)
        row_text = normalize_text(text[match.end() : end])
        row_text = dedupe_repeated_prefix(row_text)
        row_name = normalize_segment_name_text(
            infer_name_from_text(row_text, f"row-{match.group('idx')}")
        )
        comparison_subject = build_appendix_comparison_subject(
            appendix.get("title", ""),
            scope_name,
            row_name,
        )
        segments.append(
            {
                "id": f"segment-{next_index:03d}",
                "source_type": "appendix",
                "source_marker": appendix["marker"],
                "source_label": appendix["title"],
                "source_item_marker": None,
                "source_item_index": int(match.group("idx")),
                "segment_name": comparison_subject,
                "comparison_subject": comparison_subject,
                "statement_text": row_text,
                "display_statement_text": safe_statement_preview(row_text),
                "source_ref": f"{appendix['marker']} {appendix['title']} / 序号{match.group('idx')} {row_name}",
                "source_quality": appendix.get("review_priority", "normal"),
                "source_formula_sensitive": appendix_source_formula_sensitive(appendix),
                "source_table_like": False,
            }
        )
        next_index += 1
    return segments, next_index


def build_clause_segments(structured: Dict, start_index: int) -> Tuple[List[Dict], int]:
    segments: List[Dict] = []
    next_index = start_index
    for clause in structured.get("clauses", []):
        source_text = clause.get("content_markdown") or clause["text"]
        text = markdown_to_plain_text(source_text)
        if not is_parameter_clause(text):
            continue
        label = clause.get("label") or clause["marker"]
        segments.append(
            {
                "id": f"segment-{next_index:03d}",
                "source_type": "clause",
                "source_marker": clause["marker"],
                "source_label": label,
                "source_item_marker": None,
                "source_item_index": None,
                "segment_name": label,
                "comparison_subject": label,
                "statement_text": text,
                "display_statement_text": safe_statement_preview(text),
                "source_ref": f"{clause['marker']} {label}",
                "source_quality": "formula_sensitive" if clause.get("formula_sensitive") else "normal",
                "source_formula_sensitive": clause.get("formula_sensitive", False),
                "source_table_like": is_table_like_statement(text),
            }
        )
        next_index += 1
    return segments, next_index


def collect_parameter_segments(structured: Dict) -> List[Dict]:
    segments: List[Dict] = []
    next_index = 1
    for appendix in structured.get("appendices", []):
        if not looks_like_parameter_appendix(appendix):
            continue
        if appendix["marker"] in {"附录3", "附录三", "附件3", "附件三"}:
            appendix_segments, next_index = build_appendix3_segments(appendix, next_index)
        else:
            appendix_segments, next_index = build_table_segments(appendix, next_index)
        segments.extend(appendix_segments)
    clause_segments, next_index = build_clause_segments(structured, next_index)
    segments.extend(clause_segments)
    return segments


def infer_subject_context(statement: str, start: int) -> str:
    window = statement[max(0, start - 36) : start]
    matches = list(SUBJECT_RE.finditer(window))
    if not matches:
        return ""
    return normalize_text(matches[-1].group(0))


def infer_label_text(statement: str, start: int, segment_name: str) -> str:
    short_window = statement[max(0, start - 28) : start]
    short_window = re.sub(r".*[，；。：:、]\s*", "", short_window)
    short_window = short_window.strip()
    short_window = re.sub(r"(为|取|应在|按照|等于|不超过|不少于|不得小于|不得大于|应不低于|应小于等于)\s*$", "", short_window)
    short_window = short_window.strip(" ，、")

    subject = infer_subject_context(statement, start)
    if subject and subject not in short_window:
        short_window = f"{subject}{short_window}"

    if short_window.endswith("乘以") or "按实际响应容量乘以" in short_window:
        return f"{segment_name}补偿系数"

    if any(keyword in short_window for keyword in ROLE_KEYWORDS):
        return short_window
    return segment_name


def parse_numeric_list(value_text: str) -> List[float]:
    values = []
    for item in re.findall(r"-?\d+(?:\.\d+)?(?:e[+-]?\d+)?", value_text):
        try:
            values.append(float(item))
        except ValueError:
            continue
    return values


def compact_value_text(text: str) -> str:
    return re.sub(r"\s+", "", text)


def overlaps(span: Tuple[int, int], used_spans: Sequence[Tuple[int, int]]) -> bool:
    for used_start, used_end in used_spans:
        if span[0] < used_end and used_start < span[1]:
            return True
    return False


def looks_like_reference(statement: str, start: int, value: str, unit: str) -> bool:
    prefix = statement[max(0, start - 4) : start]
    suffix = statement[start : start + len(value) + 4]
    if unit:
        return False
    if ":" in value:
        return False
    if prefix.endswith(("附录", "附件")) or prefix.endswith("第"):
        return True
    if "〔" in prefix or "号" in suffix or "年" in suffix:
        return True
    if value.startswith(STOP_PREFIXES):
        return True
    return False


def estimate_confidence(
    statement: str,
    source_quality: str,
    unit: str,
    label: str,
    source_type: str,
    source_table_like: bool,
) -> str:
    if source_quality == "formula_sensitive" or looks_formula_sensitive_text(statement):
        return "low"
    if source_type == "clause" and source_table_like:
        return "low"
    if source_quality == "high":
        return "medium"
    if any(token in statement for token in ("?", "??", "???")):
        return "low"
    if unit or any(keyword in label for keyword in ROLE_KEYWORDS):
        return "high"
    return "medium"


def normalize_comparison_family_label(parameter_name: str, label: str) -> str:
    normalized_name = normalize_text(parameter_name)
    normalized_label = normalize_text(label)

    if normalized_name == "机组启动费用":
        for phase in ("冷态启动上限", "温态启动上限", "热态启动上限"):
            if phase in normalized_label:
                return phase

    if normalized_name == "现货市场申报价格限值":
        if "下限" in normalized_label:
            return "申报价格下限"
        if "上限" in normalized_label:
            return "申报价格上限"

    if normalized_name == "现货市场出清价格限值":
        if "下限" in normalized_label:
            return "出清价格下限"
        if "上限" in normalized_label:
            return "出清价格上限"

    return normalized_label


def build_parameter_item(
    item_index: int,
    segment: Dict,
    document: Dict,
    statement: str,
    label: str,
    value_text: str,
    unit: str,
    value_type: str,
) -> Dict:
    category = detect_parameter_category(label, unit, value_type)
    comparison_subject = segment.get("comparison_subject") or segment["segment_name"]
    comparison_family_label = normalize_comparison_family_label(
        comparison_subject, label
    )
    comparison_key = normalize_key_text(
        f"{comparison_subject}|{label}|{unit or value_type}"
    )
    comparison_family_key = normalize_key_text(
        f"{comparison_subject}|{comparison_family_label}|{unit or value_type}"
    )
    formula_sensitive = looks_formula_sensitive_text(statement) or segment.get(
        "source_formula_sensitive", False
    )
    table_like = bool(
        segment.get("source_type") == "clause" and segment.get("source_table_like")
    )
    confidence = estimate_confidence(
        statement,
        segment["source_quality"],
        unit,
        label,
        segment.get("source_type", ""),
        table_like,
    )
    review_reasons: List[str] = []
    if formula_sensitive:
        review_reasons.append("formula_sensitive")
    if table_like:
        review_reasons.append("table_like_clause")
    if confidence == "low":
        review_reasons.append("low_confidence")
    return {
        "id": f"parameter-{item_index:04d}",
        "segment_id": segment["id"],
        "source_document_id": document["id"],
        "source_version_label": document["version_label"],
        "source_type": segment["source_type"],
        "source_marker": segment["source_marker"],
        "source_label": segment["source_label"],
        "source_ref": segment["source_ref"],
        "parameter_name": segment["segment_name"],
        "parameter_category": category,
        "context_label": label,
        "comparison_key": comparison_key,
        "comparison_family_label": comparison_family_label,
        "comparison_family_key": comparison_family_key,
        "value_type": value_type,
        "value_text": value_text,
        "numeric_values": parse_numeric_list(value_text),
        "unit": unit,
        "statement_text": statement,
        "display_statement_text": safe_statement_preview(statement),
        "formula_sensitive": formula_sensitive,
        "table_like": table_like,
        "confidence": confidence,
        "review_reasons": review_reasons,
    }


def extract_parameter_items(segments: Iterable[Dict], document: Dict) -> List[Dict]:
    items: List[Dict] = []
    next_index = 1

    for segment in segments:
        cleaned_statement = normalize_text(segment["statement_text"])
        for statement in split_statements(cleaned_statement):
            if should_skip_statement(statement):
                continue
            startup_matches = list(STARTUP_FEE_BAND_RE.finditer(statement))
            if startup_matches:
                for match in startup_matches:
                    band = compact_value_text(match.group("band"))
                    for phase_key, phase_label in (
                        ("cold", "冷态启动上限"),
                        ("warm", "温态启动上限"),
                        ("hot", "热态启动上限"),
                    ):
                        items.append(
                            build_parameter_item(
                                next_index,
                                segment,
                                document,
                                statement,
                                f"{band}{phase_label}",
                                compact_value_text(match.group(phase_key)),
                                "万元/次",
                                "single",
                            )
                        )
                        next_index += 1
                continue

            base_unit_match = UNIT_HINT_RE.search(statement)
            base_unit = base_unit_match.group(1) if base_unit_match else ""
            used_spans: List[Tuple[int, int]] = []

            for match in RANGE_RE.finditer(statement):
                span = match.span()
                label = infer_label_text(statement, match.start(), segment["segment_name"])
                value_text = match.group(0).replace(" ", "")
                unit = match.group("unit2") or match.group("unit1") or base_unit
                if looks_like_reference(statement, match.start(), value_text, unit):
                    continue
                items.append(
                    build_parameter_item(
                        next_index,
                        segment,
                        document,
                        statement,
                        label,
                        value_text,
                        unit,
                        "range_percent" if "%" in value_text else "range",
                    )
                )
                next_index += 1
                used_spans.append(span)

            for match in TIME_POINT_RE.finditer(statement):
                span = match.span()
                if overlaps(span, used_spans):
                    continue
                label = infer_label_text(statement, match.start(), segment["segment_name"])
                items.append(
                    build_parameter_item(
                        next_index,
                        segment,
                        document,
                        statement,
                        label,
                        match.group("value"),
                        "time_point",
                        "time_point",
                    )
                )
                next_index += 1
                used_spans.append(span)

            for match in SINGLE_VALUE_RE.finditer(statement):
                span = match.span()
                if overlaps(span, used_spans):
                    continue
                value = match.group("value")
                unit = match.group("unit") or base_unit
                label = infer_label_text(statement, match.start(), segment["segment_name"])
                if looks_like_reference(statement, match.start(), value, unit):
                    continue
                if not unit and not any(keyword in label for keyword in ROLE_KEYWORDS):
                    continue
                items.append(
                    build_parameter_item(
                        next_index,
                        segment,
                        document,
                        statement,
                        label,
                        f"{value}{unit}".strip(),
                        unit,
                        "single",
                    )
                )
                next_index += 1
                used_spans.append(span)

    deduped: List[Dict] = []
    seen = set()
    for item in items:
        dedupe_key = (
            item["source_ref"],
            item["comparison_key"],
            item["value_text"],
            item["statement_text"],
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        deduped.append(item)
    return deduped


def build_review_candidates(segments: Iterable[Dict], items: Iterable[Dict]) -> List[Dict]:
    candidates: List[Dict] = []
    seen = set()

    for segment in segments:
        reason_codes: List[str] = []
        if segment.get("source_formula_sensitive"):
            reason_codes.append("formula_sensitive_source")
        if segment.get("source_type") == "clause" and segment.get("source_table_like"):
            reason_codes.append("table_like_clause_source")
        if not reason_codes:
            continue
        dedupe_key = ("segment", segment.get("source_ref"), tuple(reason_codes))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        candidates.append(
            {
                "kind": "segment",
                "source_ref": segment.get("source_ref"),
                "parameter_name": segment.get("segment_name"),
                "context_label": segment.get("source_label"),
                "value_text": None,
                "reason_codes": reason_codes,
                "statement_preview": safe_statement_preview(segment.get("statement_text", "")),
            }
        )

    for item in items:
        reason_codes = list(item.get("review_reasons") or [])
        if not reason_codes:
            continue
        dedupe_key = (
            "item",
            item.get("source_ref"),
            item.get("context_label"),
            item.get("value_text"),
            tuple(reason_codes),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        candidates.append(
            {
                "kind": "parameter_item",
                "source_ref": item.get("source_ref"),
                "parameter_name": item.get("parameter_name"),
                "context_label": item.get("context_label"),
                "value_text": item.get("value_text"),
                "reason_codes": reason_codes,
                "statement_preview": item.get("display_statement_text"),
            }
        )

    return candidates


def build_catalog(structured: Dict) -> Dict:
    document = structured["document"]
    segments = collect_parameter_segments(structured)
    items = extract_parameter_items(segments, document)
    review_candidates = build_review_candidates(segments, items)
    return {
        "document": {
            "id": document["id"],
            "title": document["title"],
            "version_label": document["version_label"],
            "rule_type": document["rule_type"],
            "source_path": document["source_path"],
        },
        "catalog_summary": {
            "segment_count": len(segments),
            "parameter_item_count": len(items),
            "formula_sensitive_item_count": sum(
                1 for item in items if item.get("formula_sensitive")
            ),
            "appendix_segment_count": sum(1 for item in segments if item["source_type"] == "appendix"),
            "clause_segment_count": sum(1 for item in segments if item["source_type"] == "clause"),
            "formula_sensitive_segment_count": sum(
                1 for item in segments if item.get("source_formula_sensitive")
            ),
            "table_like_clause_segment_count": sum(
                1
                for item in segments
                if item.get("source_type") == "clause" and item.get("source_table_like")
            ),
            "high_confidence_item_count": sum(1 for item in items if item["confidence"] == "high"),
            "medium_confidence_item_count": sum(1 for item in items if item["confidence"] == "medium"),
            "low_confidence_item_count": sum(1 for item in items if item["confidence"] == "low"),
            "review_candidate_count": len(review_candidates),
        },
        "parameter_segments": segments,
        "parameter_items": items,
        "review_candidates": review_candidates,
    }


def group_by_key(items: Iterable[Dict]) -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = {}
    for item in items:
        if item.get("formula_sensitive") or item.get("confidence") == "low":
            continue
        grouped.setdefault(item["comparison_key"], []).append(item)
    return grouped


def blocked_review_keys(items: Iterable[Dict]) -> set[str]:
    keys: set[str] = set()
    for item in items:
        if item.get("formula_sensitive") or item.get("confidence") == "low":
            comparison_key = item.get("comparison_key")
            if comparison_key:
                keys.add(comparison_key)
    return keys


def group_by_family_key(items: Iterable[Dict]) -> Dict[str, List[Dict]]:
    grouped: Dict[str, List[Dict]] = {}
    for item in items:
        family_key = item.get("comparison_family_key") or item.get("comparison_key")
        if not family_key:
            continue
        grouped.setdefault(family_key, []).append(item)
    return grouped


def sort_items_for_display(items: Iterable[Dict]) -> List[Dict]:
    return sorted(
        items,
        key=lambda item: (
            item["source_marker"],
            item["parameter_name"],
            item["context_label"],
            item["value_text"],
        ),
    )


def compare_catalogs(old_catalog: Dict, new_catalog: Dict) -> Dict:
    old_review_keys = blocked_review_keys(old_catalog["parameter_items"])
    new_review_keys = blocked_review_keys(new_catalog["parameter_items"])
    blocked_keys = old_review_keys | new_review_keys

    old_grouped = {
        key: items
        for key, items in group_by_key(old_catalog["parameter_items"]).items()
        if key not in blocked_keys
    }
    new_grouped = {
        key: items
        for key, items in group_by_key(new_catalog["parameter_items"]).items()
        if key not in blocked_keys
    }

    changed: List[Dict] = []
    added: List[Dict] = []
    removed: List[Dict] = []
    unchanged: List[Dict] = []
    leftover_old: List[Dict] = []
    leftover_new: List[Dict] = []

    all_keys = sorted(set(old_grouped) | set(new_grouped))
    for key in all_keys:
        old_items = sort_items_for_display(old_grouped.get(key, []))
        new_items = sort_items_for_display(new_grouped.get(key, []))
        old_values = [item["value_text"] for item in old_items]
        new_values = [item["value_text"] for item in new_items]

        if old_items and new_items:
            if old_values == new_values:
                unchanged.append(
                    {
                        "comparison_key": key,
                        "reference": new_items[0]["source_ref"],
                        "parameter_name": new_items[0]["parameter_name"],
                        "context_label": new_items[0]["context_label"],
                        "values": new_values,
                    }
                )
            else:
                changed.append(
                    {
                        "comparison_key": key,
                        "comparison_mode": "exact",
                        "parameter_name": new_items[0]["parameter_name"],
                        "context_label": new_items[0]["comparison_family_label"]
                        or new_items[0]["context_label"],
                        "old_items": old_items,
                        "new_items": new_items,
                    }
                )
        elif new_items:
            leftover_new.extend(new_items)
        else:
            leftover_old.extend(old_items)

    old_family_grouped = group_by_family_key(leftover_old)
    new_family_grouped = group_by_family_key(leftover_new)
    consumed_old_ids: set[str] = set()
    consumed_new_ids: set[str] = set()

    for family_key in sorted(set(old_family_grouped) & set(new_family_grouped)):
        old_items = sort_items_for_display(old_family_grouped[family_key])
        new_items = sort_items_for_display(new_family_grouped[family_key])
        changed.append(
            {
                "comparison_key": family_key,
                "comparison_mode": "family_group",
                "parameter_name": new_items[0]["parameter_name"],
                "context_label": new_items[0]["comparison_family_label"]
                or new_items[0]["context_label"],
                "old_items": old_items,
                "new_items": new_items,
            }
        )
        consumed_old_ids.update(item["id"] for item in old_items)
        consumed_new_ids.update(item["id"] for item in new_items)

    for item in leftover_new:
        if item["id"] in consumed_new_ids:
            continue
        added.append(item)
    for item in leftover_old:
        if item["id"] in consumed_old_ids:
            continue
        removed.append(item)

    return {
        "old_document": old_catalog["document"],
        "new_document": new_catalog["document"],
        "summary": {
            "changed_count": len(changed),
            "added_count": len(added),
            "removed_count": len(removed),
            "unchanged_count": len(unchanged),
            "review_blocked_key_count": len(blocked_keys),
            "review_blocked_item_count": sum(
                1
                for item in old_catalog["parameter_items"] + new_catalog["parameter_items"]
                if item.get("comparison_key") in blocked_keys
            ),
        },
        "changed_items": changed,
        "added_items": sort_items_for_display(added),
        "removed_items": sort_items_for_display(removed),
        "unchanged_items": unchanged,
    }


def build_compare_markdown(diff: Dict) -> str:
    old_doc = diff["old_document"]
    new_doc = diff["new_document"]
    summary = diff["summary"]

    lines = [
        f"# {old_doc['title']} 参数差异样板",
        "",
        "## 对比范围",
        f"- 旧版本：`{old_doc['version_label']}`",
        f"- 新版本：`{new_doc['version_label']}`",
        f"- 规则类型：`{new_doc['rule_type']}`",
        "",
        "## 差异摘要",
        f"- 明确数值变化：`{summary['changed_count']}`",
        f"- 新增参数项：`{summary['added_count']}`",
        f"- 删除参数项：`{summary['removed_count']}`",
        f"- 未变化参数项：`{summary['unchanged_count']}`",
        f"- 转入复核池、未纳入正式差异：`{summary.get('review_blocked_item_count', 0)}` 条记录 / `{summary.get('review_blocked_key_count', 0)}` 个比较键",
        "",
        "## 说明",
        "- 本报告用于提炼版本间可直接核对的数值、阈值、时间点和次数变化，不等同于全文逐字比对。",
        "- 对于公式密集、符号复杂的计算段落，本报告不直接拆解为前端参数表，避免把公式碎片误识别为数值变化。",
        "- 若某个参数键在任一版本中已被标记为公式敏感或低置信度，则该键整体转入复核池，不再强行记作正式新增或删除。",
        "- 若同一业务口径由“分别规定”调整为“统一规定”，页面上可能表现为“旧项删除 + 新项新增”。",
        "",
    ]

    lines.append("## 一、明确数值变化")
    if diff["changed_items"]:
        for item in diff["changed_items"]:
            old_values = " / ".join(
                f"{old['context_label']}={old['value_text']}" for old in item["old_items"]
            )
            new_values = " / ".join(
                f"{new['context_label']}={new['value_text']}" for new in item["new_items"]
            )
            lines.append(f"### {item['parameter_name']} | {item['context_label']}")
            lines.append(f"- 旧值：`{old_values}`")
            lines.append(f"- 新值：`{new_values}`")
            lines.append(f"- 旧来源：`{item['old_items'][0]['source_ref']}`")
            lines.append(f"- 新来源：`{item['new_items'][0]['source_ref']}`")
            lines.append("")
    else:
        lines.append("- 未识别到可直接按同键比对的数值变化。")
        lines.append("")

    lines.append("## 二、新增参数项")
    if diff["added_items"]:
        for item in diff["added_items"]:
            lines.append(f"- `{item['source_ref']}` | `{item['context_label']}` -> `{item['value_text']}`")
    else:
        lines.append("- 无")
    lines.append("")

    lines.append("## 三、删除参数项")
    if diff["removed_items"]:
        for item in diff["removed_items"]:
            lines.append(f"- `{item['source_ref']}` | `{item['context_label']}` -> `{item['value_text']}`")
    else:
        lines.append("- 无")
    lines.append("")

    return "\n".join(lines).strip() + "\n"


def write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_build(args: argparse.Namespace) -> int:
    input_path = resolve_path(args.input)
    output_path = resolve_path(args.output)
    structured = json.loads(input_path.read_text(encoding="utf-8"))
    catalog = build_catalog(structured)
    write_json(output_path, catalog)
    print(f"Resolved input: {input_path}")
    print(f"Catalog written: {output_path}")
    print(
        "Summary: "
        f"segments={catalog['catalog_summary']['segment_count']}, "
        f"items={catalog['catalog_summary']['parameter_item_count']}"
    )
    return 0


def run_compare(args: argparse.Namespace) -> int:
    old_path = resolve_path(args.old)
    new_path = resolve_path(args.new)
    output_json = resolve_path(args.output_json)
    output_md = resolve_path(args.output_md)

    old_catalog = json.loads(old_path.read_text(encoding="utf-8"))
    new_catalog = json.loads(new_path.read_text(encoding="utf-8"))
    diff = compare_catalogs(old_catalog, new_catalog)

    write_json(output_json, diff)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text(build_compare_markdown(diff), encoding="utf-8")

    print(f"Resolved old catalog: {old_path}")
    print(f"Resolved new catalog: {new_path}")
    print(f"Diff JSON written: {output_json}")
    print(f"Diff Markdown written: {output_md}")
    print(
        "Summary: "
        f"changed={diff['summary']['changed_count']}, "
        f"added={diff['summary']['added_count']}, "
        f"removed={diff['summary']['removed_count']}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build and compare parameter catalogs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build a parameter catalog from structured JSON")
    build_parser.add_argument("--input", required=True, help="Structured JSON input path")
    build_parser.add_argument("--output", required=True, help="Parameter catalog output path")
    build_parser.set_defaults(func=run_build)

    compare_parser = subparsers.add_parser("compare", help="Compare two parameter catalogs")
    compare_parser.add_argument("--old", required=True, help="Old version catalog path")
    compare_parser.add_argument("--new", required=True, help="New version catalog path")
    compare_parser.add_argument("--output-json", required=True, help="Diff JSON output path")
    compare_parser.add_argument("--output-md", required=True, help="Diff Markdown output path")
    compare_parser.set_defaults(func=run_compare)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
