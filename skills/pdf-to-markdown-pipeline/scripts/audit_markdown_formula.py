#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Audit generated Markdown / JSON outputs for OCR artifacts and garbled formulas.

This is a lightweight gate intended for the PDF -> Markdown / JSON pipeline:
1. detect inline page/footer artifacts leaked into正文
2. detect legacy formula glyph soup that should have been routed to公式识别
3. fail fast before downstream diff / analysis consumes bad source text
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Optional


INLINE_PAGE_FOOTER_RE = re.compile(r"第\s*\d+\s*页\s*[,，]\s*共\s*\d+\s*页")
INLINE_QQ_ARTIFACT_RE = re.compile(r"\{\s*,?\s*\d+.{0,24}?Qq\s*\d+.{0,8}?榰")
INLINE_TIMESTAMP_WATERMARK_RE = re.compile(
    r"(?:郑书杰|葫芦岛元亨能源有限公司)\s*20\d{2}年\d{1,2}月\d{1,2}日\s*\d{1,2}:\d{2}:\d{2}"
)
LEGACY_FORMULA_GLYPH_RE = re.compile(r"[]")
GARBLED_FORMULA_TOKEN_RE = re.compile(r"(?:PQPQR|PQR|QRP|QRR|QPQ|PQQ)")
ASCII_TOKEN_SOUP_RE = re.compile(
    r"(?:(?<![A-Za-z])[A-Za-z]{1,4}(?![A-Za-z])\s+){6,}(?<![A-Za-z])[A-Za-z]{0,4}"
)
MIXED_FORMULA_TOKEN_SOUP_RE = re.compile(
    r"(?<![A-Za-z])(?:[A-Z]{1,4}|\d|[a-z])(?:\s+(?:[A-Z]{1,4}|\d|[a-z])){4,}(?![A-Za-z])"
)
MINERU_HIGH_RISK_LATEX_RE = re.compile(r"(\\#|\\sharp|\\breve|\\ddot|\\not\s|☉|♯)")
MINERU_MEDIUM_RISK_LATEX_RE = re.compile(r"(\\mathbb)")
FLATTENED_FORMULA_TEXT_RE = re.compile(
    r"(?=.*(?:计算公式|费用|电量|电价|乘积))(?=.*R[\u4e00-\u9fffA-Za-z_{}\\,，]*\s*=)(?=.*t\s*=\s*0)(?=.*[TＴ])(?=.*(?:×|\\times|\*))"
)
FLATTENED_APPENDIX_TABLE_RE = re.compile(
    r"(?=.{300,})(?:(?=.*附录\s*[0-9一二三四五六七八九十])(?=.*流程图)(?=.*开始)(?=.*结束)|(?=.*编号\s*关键参数\s*取值)|(?=.*附表)(?=.*评分标准)(?=.*依据))"
)
FLATTENED_INLINE_TABLE_RE = re.compile(
    r"(?=.{300,})(?=.*(?:对应关系|评分标准|分数区间|关键参数|编号))(?=.*(?:AAA|AA|取值|优秀|优良|一般|较差))"
)
FLATTENED_PARAMETER_TABLE_HEADER_RE = re.compile(
    r"附件\s*2\s*电力市场结算参数表\s*序号\s*参数\s*参数说明\s*暂定数值"
)
MISCLASSIFIED_PARAMETER_HEADING_RE = re.compile(
    r"^#{3,6}\s+(?:\d+(?:\.\d+)?\s+)?(?:\[)?(?:\d+\s*)?"
    r"(?:L\s*(?:用户缺额|发电机组缺额)|[μµ]\s*发电企业机制电量比例系数|"
    r"M[0-9]\s*新能源场站.*准确率|[ηη][0-9]?\s*新能源.*返还费用比例系数|"
    r"[0-9]η\s*新能源.*返还费用比例系)"
)
MISCLASSIFIED_NUMERIC_HEADING_RE = re.compile(
    r"^#{3,6}\s+(?!附件)(?:\d+(?:\.\d+)?|[A-Za-z]+\d*|[A-Za-z]*\d+)\b.{0,120}$"
)
INLINE_APPENDIX_IN_CLAUSE_RE = re.compile(
    r"(?:附件\s*(?:[0-9一二三四五六七八九十]+)?\s*(?:名词解释|名称解释|.*?参数表\s*序号)|附件名词解释)"
)
PRIVATE_USE_RE = re.compile(r"[\ue000-\uf8ff]")
CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
UNRESOLVED_REVIEW_RE = re.compile(
    r"(未命中.{0,80}(?:公式识别缓存|页面识别缓存)|未配置多模态接口|页面复核已跳过|无法完整识别|未完整显示|需人工复核|仍建议人工核对|公式[^。；\n]{0,40}缺失|内容缺失)"
)
REVIEW_METADATA_RE = re.compile(r"^- (?:复核状态|识别备注|复核提示|内容来源)：")

SUSPICIOUS_UNICODE_RANGES = (
    (0x0700, 0x074F, "syriac"),
    (0x0750, 0x077F, "arabic_supplement"),
    (0x0780, 0x07BF, "thaana"),
    (0x0800, 0x083F, "samaritan"),
    (0x0840, 0x085F, "mandaic"),
    (0x08A0, 0x08FF, "arabic_extended"),
    (0xFB50, 0xFDFF, "arabic_presentation"),
    (0xFE70, 0xFEFF, "arabic_presentation"),
)


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def is_structured_output_path(path: Path) -> bool:
    normalized = str(path).replace("\\", "/")
    return "/2_结构化产物/" in normalized or normalized.startswith("2_结构化产物/")


def iter_target_files(inputs: Iterable[str], patterns: Iterable[str]) -> List[Path]:
    resolved: List[Path] = []
    seen = set()

    for raw_path in inputs:
        path = resolve_path(raw_path)
        if path.is_file():
            normalized = str(path)
            if normalized not in seen:
                seen.add(normalized)
                resolved.append(path)
        elif path.is_dir():
            for child in sorted(path.rglob("*")):
                if child.suffix.lower() not in {".md", ".markdown", ".json", ".txt"}:
                    continue
                normalized = str(child)
                if normalized not in seen:
                    seen.add(normalized)
                    resolved.append(child)

    for pattern in patterns:
        for path in sorted(Path.cwd().glob(pattern)):
            if not path.is_file():
                continue
            normalized = str(path.resolve())
            if normalized not in seen:
                seen.add(normalized)
                resolved.append(path.resolve())

    return resolved


def issue_record(
    path: Path,
    line_number: Optional[int],
    issue_type: str,
    fragment: str,
    line_text: str,
    severity: str = "P2",
    target: Optional[str] = None,
) -> Dict:
    return {
        "file": str(path),
        "line": line_number,
        "issue_type": issue_type,
        "fragment": fragment.strip(),
        "line_text": line_text.strip(),
        "severity": severity,
        "target": target,
    }


def suspicious_unicode_chars(text: str) -> List[str]:
    chars: List[str] = []
    for ch in text:
        code = ord(ch)
        if code < 128:
            continue
        for start, end, _name in SUSPICIOUS_UNICODE_RANGES:
            if start <= code <= end:
                chars.append(ch)
                break
    return chars


def scan_line(path: Path, line_number: int, line: str, strict_delivery: bool = False) -> List[Dict]:
    findings: List[Dict] = []
    text = line.rstrip("\n")

    for pattern, issue_type in (
        (INLINE_QQ_ARTIFACT_RE, "inline_page_artifact"),
        (INLINE_PAGE_FOOTER_RE, "inline_page_footer"),
        (INLINE_TIMESTAMP_WATERMARK_RE, "inline_timestamp_watermark"),
    ):
        for match in pattern.finditer(text):
            findings.append(
                issue_record(path, line_number, issue_type, match.group(0), text, severity="P1")
            )

    if GARBLED_FORMULA_TOKEN_RE.search(text):
        findings.append(
            issue_record(
                path,
                line_number,
                "garbled_formula_token",
                GARBLED_FORMULA_TOKEN_RE.search(text).group(0),
                text,
                severity="P1",
            )
        )
    if LEGACY_FORMULA_GLYPH_RE.search(text) and len(LEGACY_FORMULA_GLYPH_RE.findall(text)) >= 2:
        findings.append(
            issue_record(
                path,
                line_number,
                "legacy_formula_glyphs",
                "".join(LEGACY_FORMULA_GLYPH_RE.findall(text)[:8]),
                text,
                severity="P1",
            )
        )
    if PRIVATE_USE_RE.search(text):
        findings.append(
            issue_record(
                path,
                line_number,
                "private_use_chars",
                PRIVATE_USE_RE.search(text).group(0),
                text,
                severity="P1",
            )
        )
    control_char_match = CONTROL_CHAR_RE.search(text)
    if control_char_match:
        ch = control_char_match.group(0)
        findings.append(
            issue_record(
                path,
                line_number,
                "unexpected_control_character",
                f"U+{ord(ch):04X}",
                text,
                severity="P1",
            )
        )
    suspicious_chars = suspicious_unicode_chars(text)
    if suspicious_chars:
        unique_chars = "".join(dict.fromkeys(suspicious_chars))
        names = ", ".join(f"{ch}=U+{ord(ch):04X} {unicodedata.name(ch, 'UNKNOWN')}" for ch in unique_chars[:6])
        findings.append(
            issue_record(
                path,
                line_number,
                "suspicious_unicode_formula_chars",
                names,
                text,
                severity="P1",
            )
        )
    ascii_token_match = ASCII_TOKEN_SOUP_RE.search(text) or MIXED_FORMULA_TOKEN_SOUP_RE.search(text)
    if ascii_token_match:
        findings.append(
            issue_record(
                path,
                line_number,
                "ascii_formula_token_soup",
                ascii_token_match.group(0),
                text,
                severity="P1",
            )
        )
    mineru_high_risk_match = MINERU_HIGH_RISK_LATEX_RE.search(text)
    if mineru_high_risk_match:
        findings.append(
            issue_record(
                path,
                line_number,
                "mineru_high_risk_latex_token",
                mineru_high_risk_match.group(0),
                text,
                severity="P1",
            )
        )
    mineru_medium_risk_match = MINERU_MEDIUM_RISK_LATEX_RE.search(text)
    if mineru_medium_risk_match:
        findings.append(
            issue_record(
                path,
                line_number,
                "mineru_possible_suspicious_latex_token",
                mineru_medium_risk_match.group(0),
                text,
                severity="P2",
            )
        )
    flattened_formula_match = FLATTENED_FORMULA_TEXT_RE.search(text)
    if flattened_formula_match:
        findings.append(
            issue_record(
                path,
                line_number,
                "flattened_formula_text",
                flattened_formula_match.group(0),
                text,
                severity="P1",
            )
        )
    flattened_appendix_table_match = FLATTENED_APPENDIX_TABLE_RE.search(text)
    if flattened_appendix_table_match:
        findings.append(
            issue_record(
                path,
                line_number,
                "flattened_appendix_table_text",
                flattened_appendix_table_match.group(0),
                text,
                severity="P1",
            )
        )
    flattened_inline_table_match = FLATTENED_INLINE_TABLE_RE.search(text)
    if flattened_inline_table_match:
        findings.append(
            issue_record(
                path,
                line_number,
                "flattened_table_text",
                flattened_inline_table_match.group(0),
                text,
                severity="P1",
            )
        )
    flattened_parameter_header_match = FLATTENED_PARAMETER_TABLE_HEADER_RE.search(text)
    if flattened_parameter_header_match:
        findings.append(
            issue_record(
                path,
                line_number,
                "flattened_parameter_table_header",
                flattened_parameter_header_match.group(0),
                text,
                severity="P1",
            )
        )
    if is_structured_output_path(path):
        misclassified_parameter_heading_match = MISCLASSIFIED_PARAMETER_HEADING_RE.search(text)
        if misclassified_parameter_heading_match:
            findings.append(
                issue_record(
                    path,
                    line_number,
                    "misclassified_parameter_table_heading",
                    misclassified_parameter_heading_match.group(0),
                    text,
                    severity="P1",
                )
            )
        misclassified_numeric_heading_match = MISCLASSIFIED_NUMERIC_HEADING_RE.search(text)
        if misclassified_numeric_heading_match:
            findings.append(
                issue_record(
                    path,
                    line_number,
                    "misclassified_numeric_heading",
                    misclassified_numeric_heading_match.group(0),
                    text,
                    severity="P1",
                )
            )
        stripped_text = text.lstrip()
        inline_appendix_match = INLINE_APPENDIX_IN_CLAUSE_RE.search(text)
        if inline_appendix_match:
            if not (
                stripped_text.startswith("### 附件")
                or stripped_text.startswith("## 附录")
                or stripped_text.startswith("附件 ")
            ):
                findings.append(
                    issue_record(
                        path,
                        line_number,
                        "inline_appendix_text_in_clause",
                        inline_appendix_match.group(0),
                        text,
                        severity="P1",
                    )
                )
    if strict_delivery:
        if REVIEW_METADATA_RE.search(text):
            findings.append(
                issue_record(
                    path,
                    line_number,
                    "review_metadata_in_delivery_markdown",
                    text,
                    text,
                    severity="P2",
                )
            )
        if UNRESOLVED_REVIEW_RE.search(text):
            findings.append(
                issue_record(
                    path,
                    line_number,
                    "unresolved_review_note_in_delivery",
                    UNRESOLVED_REVIEW_RE.search(text).group(0),
                    text,
                    severity="P1",
                )
            )
    return findings


def scan_text_file(path: Path, strict_delivery: bool = False) -> List[Dict]:
    findings: List[Dict] = []
    text = path.read_text(encoding="utf-8")
    for match in CONTROL_CHAR_RE.finditer(text):
        line_number = text.count("\n", 0, match.start()) + 1
        line_start = text.rfind("\n", 0, match.start()) + 1
        line_end = text.find("\n", match.start())
        if line_end == -1:
            line_end = len(text)
        findings.append(
            issue_record(
                path,
                line_number,
                "unexpected_control_character",
                f"U+{ord(match.group(0)):04X}",
                text[line_start:line_end],
                severity="P1",
            )
        )

    for line_number, line in enumerate(text.splitlines(), start=1):
        findings.extend(scan_line(path, line_number, line, strict_delivery=strict_delivery))

    if text.count("$$") % 2 == 1:
        findings.append(
            {
                "file": str(path),
                "line": None,
                "issue_type": "unbalanced_block_latex",
                "fragment": "$$",
                "line_text": "File contains an odd number of $$ delimiters.",
                "severity": "P1",
                "target": None,
            }
        )
    return findings


def scan_json_string_values(path: Path, obj, findings: List[Dict], json_path: str = "") -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            scan_json_string_values(path, value, findings, f"{json_path}.{key}" if json_path else str(key))
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            scan_json_string_values(path, value, findings, f"{json_path}[{index}]")
    elif isinstance(obj, str):
        for finding in scan_line(path, None, obj, strict_delivery=False):
            finding["target"] = json_path
            findings.append(finding)


def structure_target_label(kind: str, item: Dict) -> str:
    marker = item.get("marker") or item.get("id") or ""
    label = item.get("label") or item.get("title") or ""
    return f"{kind}:{item.get('id')} {marker} {label}".strip()


def scan_structure_review_state(path: Path, payload: Dict) -> List[Dict]:
    findings: List[Dict] = []
    for node in payload.get("section_nodes") or []:
        if node.get("node_type") != "section":
            continue
        marker = str(node.get("marker") or "")
        title = str(node.get("title") or "")
        if marker and not marker.startswith("第"):
            target = structure_target_label("section", node)
            findings.append(
                issue_record(
                    path,
                    None,
                    "numeric_pseudo_section_node",
                    f"{marker} {title}".strip(),
                    f"{target} uses a numeric marker; likely a table row or wrapped paragraph parsed as a section.",
                    severity="P1",
                    target=target,
                )
            )
    for kind, items in (("clause", payload.get("clauses") or []), ("appendix", payload.get("appendices") or [])):
        for item in items:
            target = structure_target_label(kind, item)
            severity = "P1" if item.get("formula_sensitive") or kind == "appendix" else "P2"
            content_source = str(item.get("content_source") or "raw_text")
            if (
                kind == "clause"
                and item.get("formula_sensitive")
                and content_source == "raw_text"
                and not item.get("content_review_required")
            ):
                findings.append(
                    issue_record(
                        path,
                        None,
                        "formula_sensitive_raw_text_unreviewed",
                        content_source,
                        f"{target} is formula_sensitive but still uses raw_text without review_required=true",
                        severity="P1",
                        target=target,
                    )
                )
            if (
                kind == "appendix"
                and (item.get("appendix_kind") == "formula_model" or item.get("formula_review_pages"))
                and content_source == "raw_text"
                and not item.get("content_review_required")
            ):
                findings.append(
                    issue_record(
                        path,
                        None,
                        "formula_appendix_raw_text_unreviewed",
                        content_source,
                        f"{target} has formula/model review signals but still uses raw_text without review_required=true",
                        severity="P1",
                        target=target,
                    )
                )
            if item.get("content_review_required"):
                findings.append(
                    issue_record(
                        path,
                        None,
                        "unresolved_content_review_required",
                        str(item.get("content_source") or ""),
                        f"{target} still has content_review_required=true",
                        severity=severity,
                        target=target,
                    )
                )
            for issue in item.get("content_issues") or []:
                issue_type = "unresolved_content_issue"
                if UNRESOLVED_REVIEW_RE.search(str(issue)):
                    issue_type = "unresolved_formula_or_page_issue"
                    severity = "P1"
                findings.append(
                    issue_record(
                        path,
                        None,
                        issue_type,
                        str(issue),
                        str(issue),
                        severity=severity,
                        target=target,
                    )
                )
    return findings


def scan_file(path: Path, strict_delivery: bool = False) -> List[Dict]:
    if path.suffix.lower() == ".json":
        findings: List[Dict] = []
        payload = json.loads(path.read_text(encoding="utf-8"))
        scan_json_string_values(path, payload, findings)
        if strict_delivery and isinstance(payload, dict):
            findings.extend(scan_structure_review_state(path, payload))
        return findings
    return scan_text_file(path, strict_delivery=strict_delivery)


def build_markdown_report(summary: Dict, findings: List[Dict]) -> str:
    lines = [
        "# Markdown / JSON OCR 审计报告",
        "",
        f"- 扫描文件数：{summary['file_count']}",
        f"- 问题总数：{summary['finding_count']}",
        "",
        "## 问题类型统计",
        "",
        "| 类型 | 数量 |",
        "| --- | ---: |",
    ]
    for issue_type, count in summary["counts_by_type"].items():
        lines.append(f"| {issue_type} | {count} |")

    lines.extend(["", "## 明细", "", "| 优先级 | 文件 | 行号 | 类型 | 对象 | 片段 |", "| --- | --- | ---: | --- | --- | --- |"])
    for finding in findings:
        line_text = str(finding.get("fragment") or "").replace("\n", " ")
        lines.append(
            f"| {finding.get('severity', 'P2')} | {finding['file']} | {finding.get('line') or ''} | {finding['issue_type']} | {finding.get('target') or ''} | {line_text} |"
        )
    return "\n".join(lines).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Markdown / JSON OCR artifacts and formula corruption")
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        help="Input file or directory. Repeat for multiple inputs.",
    )
    parser.add_argument(
        "--glob",
        action="append",
        default=[],
        help="Glob pattern relative to cwd, e.g. 2_结构化产物/markdown/*.md",
    )
    parser.add_argument("--output-json", help="Optional JSON output path")
    parser.add_argument("--output-md", help="Optional Markdown output path")
    parser.add_argument(
        "--fail-on-findings",
        action="store_true",
        help="Return exit code 1 if any finding is detected",
    )
    parser.add_argument(
        "--strict-delivery",
        action="store_true",
        help="Treat review notes and unresolved structure review state as delivery-blocking findings",
    )
    args = parser.parse_args()

    targets = iter_target_files(args.input, args.glob)
    if not targets:
        raise SystemExit("No input files resolved. Pass --input or --glob.")

    findings: List[Dict] = []
    for path in targets:
        findings.extend(scan_file(path, strict_delivery=args.strict_delivery))

    counts_by_type: Dict[str, int] = {}
    counts_by_severity: Dict[str, int] = {}
    for finding in findings:
        counts_by_type[finding["issue_type"]] = counts_by_type.get(finding["issue_type"], 0) + 1
        severity = finding.get("severity", "P2")
        counts_by_severity[severity] = counts_by_severity.get(severity, 0) + 1

    summary = {
        "file_count": len(targets),
        "finding_count": len(findings),
        "counts_by_type": dict(sorted(counts_by_type.items())),
        "counts_by_severity": dict(sorted(counts_by_severity.items())),
        "files": [str(path) for path in targets],
    }
    payload = {"summary": summary, "findings": findings}

    if args.output_json:
        output_json = resolve_path(args.output_json)
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.output_md:
        output_md = resolve_path(args.output_md)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(build_markdown_report(summary, findings), encoding="utf-8")

    print(f"Scanned files: {len(targets)}")
    print(f"Findings: {len(findings)}")
    for severity, count in summary["counts_by_severity"].items():
        print(f"  {severity}: {count}")
    for issue_type, count in summary["counts_by_type"].items():
        print(f"  {issue_type}: {count}")

    return 1 if args.fail_on_findings and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
