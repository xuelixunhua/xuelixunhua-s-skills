#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build and patch policy-document evidence JSON.

Evidence JSON is the reusable primitive behind Markdown / business JSON:
it records where each extracted object came from, how risky it is, and what
must be reviewed before downstream diff, analysis, frontend, or QA consumes it.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import audit_markdown_formula
import pdf_toolkit


SCHEMA_VERSION = "policy_document_evidence.v1"
TEXT_PREVIEW_LIMIT = 360
TABLE_SIGNAL_RE = re.compile(r"(参数|表\s*\d+|取值|范围|单位|上限|下限|阈值|比例|系数)")
NUMERIC_TOKEN_RE = re.compile(r"\d+(?:\.\d+)?%?")
RESOLVED_CLAUSE_SOURCES = {
    "multimodal_formula",
    "manual_pdf_formula_backfill",
    "manual_formula_backfill",
    "agent_vision_formula_backfill",
    "agent_vision_no_formula_required",
}
RESOLVED_APPENDIX_SOURCES = {
    "multimodal_page_review",
    "manual_formula_backfill",
    "manual_table_backfill",
    "agent_vision_formula_backfill",
    "agent_vision_table_backfill",
    "agent_vision_no_formula_required",
    "agent_vision_no_table_required",
}
LOW_INFORMATION_PAGE_FLAGS = {"very_low_text"}
LOW_INFORMATION_REVIEW_SIGNAL_RE = re.compile(r"(公式|参数|附表|表\s*\d+|取值|计算|[=∑Σ+\-*/÷×])")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_path(raw_path: str | None) -> Optional[Path]:
    if not raw_path:
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def sha256_file(path: Path | None) -> Optional[str]:
    if not path or not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


def preview(text: str, limit: int = TEXT_PREVIEW_LIMIT) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "..."


def page_reports_by_page(report: Dict) -> Dict[int, Dict]:
    return {int(item["page"]): item for item in report.get("page_reports", []) if item.get("page")}


def classify_block(text: str, rect, y0: float) -> str:
    if pdf_toolkit.is_footer_block_text(text):
        return "footer"
    if y0 <= rect.y0 + rect.height * 0.08 and pdf_toolkit.is_header_block_text(text):
        return "header"
    if pdf_toolkit.looks_formula_heavy(text):
        return "formula_candidate"
    numeric_count = len(NUMERIC_TOKEN_RE.findall(text or ""))
    if TABLE_SIGNAL_RE.search(text or "") and numeric_count >= 2:
        return "table_candidate"
    return "text"


def extract_page_blocks(pdf_path: Path, report: Dict) -> List[Dict]:
    try:
        import fitz
    except Exception:
        return []

    page_reports = page_reports_by_page(report)
    pages: List[Dict] = []
    doc = fitz.open(str(pdf_path))
    try:
        for page_index in range(len(doc)):
            page_number = page_index + 1
            page = doc.load_page(page_index)
            rect = page.rect
            blocks: List[Dict] = []
            for block_index, block in enumerate(page.get_text("blocks"), start=1):
                if len(block) < 5:
                    continue
                x0, y0, x1, y1, text = block[:5]
                block_type = block[6] if len(block) > 6 else 0
                if block_type != 0:
                    continue
                cleaned = pdf_toolkit.sanitize_text(text).strip()
                if not cleaned:
                    continue
                block_kind = classify_block(cleaned, rect, y0)
                blocks.append(
                    {
                        "id": f"page-{page_number:03d}-block-{block_index:03d}",
                        "page": page_number,
                        "block_index": block_index,
                        "kind": block_kind,
                        "bbox": [round(float(x0), 2), round(float(y0), 2), round(float(x1), 2), round(float(y1), 2)],
                        "text_preview": preview(cleaned),
                        "text_hash": sha256_text(cleaned),
                        "formula_noise_score": pdf_toolkit.formula_noise_score(cleaned),
                    }
                )
            pages.append(
                {
                    "page": page_number,
                    "width": round(float(rect.width), 2),
                    "height": round(float(rect.height), 2),
                    "rotation": int(page.rotation),
                    "quality": page_reports.get(page_number, {}),
                    "blocks": blocks,
                    "review_flags": sorted(set((page_reports.get(page_number, {}) or {}).get("flags", []))),
                }
            )
    finally:
        doc.close()
    return pages


def build_clause_evidence(clauses: Iterable[Dict]) -> tuple[List[Dict], List[Dict]]:
    clause_evidence: List[Dict] = []
    formula_candidates: List[Dict] = []
    for clause in clauses:
        content = clause.get("content_markdown") or clause.get("default_markdown") or clause.get("text") or ""
        item = {
            "id": clause.get("id"),
            "marker": clause.get("marker"),
            "label": clause.get("label"),
            "page_numbers": clause.get("page_numbers") or [],
            "start_page": clause.get("start_page"),
            "end_page": clause.get("end_page"),
            "text_hash": sha256_text(clause.get("text") or ""),
            "content_hash": sha256_text(content),
            "content_source": clause.get("content_source"),
            "formula_sensitive": bool(clause.get("formula_sensitive")),
            "formula_review_pages": clause.get("formula_review_pages") or [],
            "review_required": bool(clause.get("content_review_required")),
            "issues": clause.get("content_issues") or [],
        }
        clause_evidence.append(item)

        if item["formula_sensitive"]:
            source = clause.get("content_source")
            resolved = source in RESOLVED_CLAUSE_SOURCES and not item["review_required"]
            formula_candidates.append(
                {
                    "id": f"formula-{clause.get('id')}",
                    "owner_type": "clause",
                    "owner_id": clause.get("id"),
                    "owner_label": " ".join(part for part in [clause.get("marker"), clause.get("label")] if part),
                    "page_numbers": item["formula_review_pages"] or item["page_numbers"],
                    "bbox": None,
                    "status": "accepted" if resolved else "candidate",
                    "source": source or "formula_sensitive_clause",
                    "latex": None,
                    "confidence": None,
                    "text_preview": preview(content),
                    "review_required": not resolved,
                    "issues": [] if resolved else item["issues"] or ["公式敏感条款需要确认 LaTeX、变量解释和原图证据。"],
                }
            )
    return clause_evidence, formula_candidates


def build_appendix_evidence(appendices: Iterable[Dict]) -> tuple[List[Dict], List[Dict]]:
    appendix_evidence: List[Dict] = []
    table_candidates: List[Dict] = []
    for appendix in appendices:
        content = appendix.get("content_markdown") or appendix.get("content") or ""
        item = {
            "id": appendix.get("id"),
            "marker": appendix.get("marker"),
            "title": appendix.get("title"),
            "appendix_kind": appendix.get("appendix_kind"),
            "physical_start_page": appendix.get("physical_start_page") or appendix.get("page"),
            "physical_end_page": appendix.get("physical_end_page") or appendix.get("page"),
            "content_hash": sha256_text(content),
            "content_source": appendix.get("content_source"),
            "review_required": bool(appendix.get("content_review_required")),
            "issues": appendix.get("content_issues") or [],
        }
        appendix_evidence.append(item)
        if item["appendix_kind"] in {"parameter", "formula_model"} or TABLE_SIGNAL_RE.search(content):
            resolved = item["content_source"] in RESOLVED_APPENDIX_SOURCES and not item["review_required"]
            start_page = int(item["physical_start_page"] or 0)
            end_page = int(item["physical_end_page"] or start_page or 0)
            table_candidates.append(
                {
                    "id": f"table-{appendix.get('id')}",
                    "owner_type": "appendix",
                    "owner_id": appendix.get("id"),
                    "owner_label": " ".join(part for part in [appendix.get("marker"), appendix.get("title")] if part),
                    "page_numbers": [page for page in range(start_page, end_page + 1) if page > 0],
                    "bbox": None,
                    "status": "accepted" if resolved else "candidate",
                    "source": item["content_source"] or "appendix_table_or_model",
                    "structured_table": None,
                    "confidence": None,
                    "text_preview": preview(content),
                    "review_required": not resolved,
                    "issues": [] if resolved else item["issues"] or ["参数/模型附录需要确认表格结构、单元格和内嵌公式。"],
                }
            )
    return appendix_evidence, table_candidates


def normalize_mineru_seed(seed: Dict) -> tuple[Dict, List[Dict], List[Dict], List[Dict]]:
    formula_candidates: List[Dict] = []
    table_candidates: List[Dict] = []
    image_candidates: List[Dict] = []

    for item in seed.get("formula_candidates") or []:
        latex = item.get("latex") or ""
        formula_candidates.append(
            {
                "id": f"mineru-{item.get('id')}",
                "owner_type": "mineru_block",
                "owner_id": item.get("block_id"),
                "owner_label": item.get("block_id"),
                "page_numbers": item.get("page_numbers") or [],
                "bbox": item.get("bbox"),
                "status": item.get("status") or ("candidate" if item.get("review_required") else "accepted"),
                "source": item.get("source") or "mineru_equation",
                "latex": latex,
                "confidence": item.get("confidence"),
                "text_preview": preview(latex),
                "review_required": bool(item.get("review_required")),
                "issues": item.get("issues") or ([] if not item.get("review_required") else ["MinerU 公式候选需要复核。"]),
                "img_path": item.get("img_path"),
            }
        )

    for item in seed.get("table_candidates") or []:
        html = item.get("html") or ""
        table_candidates.append(
            {
                "id": f"mineru-{item.get('id')}",
                "owner_type": "mineru_block",
                "owner_id": item.get("block_id"),
                "owner_label": item.get("block_id"),
                "page_numbers": item.get("page_numbers") or [],
                "bbox": item.get("bbox"),
                "status": item.get("status") or "candidate",
                "source": item.get("source") or "mineru_table",
                "structured_table": None,
                "confidence": item.get("confidence"),
                "text_preview": preview(html),
                "review_required": bool(item.get("review_required", True)),
                "issues": item.get("issues") or ["MinerU 表格候选需要复核。"],
                "html": html,
                "img_path": item.get("img_path"),
            }
        )

    for item in seed.get("image_candidates") or []:
        image_candidates.append(
            {
                "id": f"mineru-{item.get('id')}",
                "owner_type": "mineru_block",
                "owner_id": item.get("block_id"),
                "owner_label": item.get("block_id"),
                "page_numbers": item.get("page_numbers") or [],
                "bbox": item.get("bbox"),
                "status": item.get("status") or "candidate",
                "source": item.get("source") or "mineru_image",
                "img_path": item.get("img_path"),
                "review_required": bool(item.get("review_required", True)),
                "issues": item.get("issues") or ["MinerU 图片候选需要复核。"],
            }
        )

    summary = {
        "schema_version": seed.get("schema_version"),
        "seed_json_path": seed.get("seed_json_path"),
        "source_pdf": seed.get("source_pdf"),
        "auto_dir": seed.get("auto_dir"),
        "first_page_number": seed.get("first_page_number"),
        "artifacts": seed.get("artifacts") or {},
        "counts": seed.get("counts") or {},
        "block_count": len(seed.get("blocks") or []),
        "formula_candidate_count": len(formula_candidates),
        "table_candidate_count": len(table_candidates),
        "image_candidate_count": len(image_candidates),
    }
    return summary, formula_candidates, table_candidates, image_candidates


def build_audit_issues(markdown_path: Path | None) -> List[Dict]:
    if not markdown_path or not markdown_path.exists():
        return []
    findings = audit_markdown_formula.scan_file(markdown_path)
    issues: List[Dict] = []
    for index, finding in enumerate(findings, start=1):
        issues.append(
            {
                "id": f"audit-{index:04d}",
                "status": "open",
                "source": "audit_markdown_formula",
                "file": finding.get("file"),
                "line": finding.get("line"),
                "issue_type": finding.get("issue_type"),
                "fragment": finding.get("fragment"),
                "line_text": finding.get("line_text"),
                "review_required": True,
            }
        )
    return issues


def build_review_queue(evidence: Dict) -> List[Dict]:
    queue: List[Dict] = []
    for page in evidence.get("pages", []):
        quality = page.get("quality") or {}
        if quality.get("likely_needs_ocr"):
            flags = set(quality.get("flags") or [])
            text_preview = "".join(str(block.get("text_preview") or "") for block in page.get("blocks") or [])
            low_information_only = (
                quality.get("suggested_action") == "ocr_review"
                and not quality.get("formula_like")
                and flags
                and flags <= LOW_INFORMATION_PAGE_FLAGS
                and int(quality.get("char_count") or 0) <= 80
                and not LOW_INFORMATION_REVIEW_SIGNAL_RE.search(text_preview)
            )
            if low_information_only:
                continue
            queue.append(
                {
                    "id": f"review-page-{page['page']:03d}",
                    "priority": "high" if quality.get("suggested_action") == "ocr_and_formula_review" else "normal",
                    "target_type": "page",
                    "target_id": page["page"],
                    "page_numbers": [page["page"]],
                    "reason": "页面质量报告建议 OCR/人工复核。",
                }
            )
    for formula in evidence.get("formula_candidates", []):
        if formula.get("status") not in {"resolved", "accepted"}:
            queue.append(
                {
                    "id": f"review-{formula['id']}",
                    "priority": "high",
                    "target_type": "formula_candidate",
                    "target_id": formula["id"],
                    "page_numbers": formula.get("page_numbers") or [],
                    "reason": "; ".join(formula.get("issues") or ["公式候选需要复核。"]),
                }
            )
    for table in evidence.get("table_candidates", []):
        if table.get("status") not in {"resolved", "accepted"}:
            queue.append(
                {
                    "id": f"review-{table['id']}",
                    "priority": "high" if table.get("source") == "appendix_table_or_model" else "normal",
                    "target_type": "table_candidate",
                    "target_id": table["id"],
                    "page_numbers": table.get("page_numbers") or [],
                    "reason": "; ".join(table.get("issues") or ["表格候选需要复核。"]),
                }
            )
    for image in evidence.get("image_candidates", []):
        if image.get("status") not in {"resolved", "accepted"}:
            queue.append(
                {
                    "id": f"review-{image['id']}",
                    "priority": "normal",
                    "target_type": "image_candidate",
                    "target_id": image["id"],
                    "page_numbers": image.get("page_numbers") or [],
                    "reason": "; ".join(image.get("issues") or ["图片候选需要复核。"]),
                }
            )
    for issue in evidence.get("audit_issues", []):
        if issue.get("status") != "resolved":
            queue.append(
                {
                    "id": f"review-{issue['id']}",
                    "priority": "high" if issue.get("issue_type") in {"inline_page_artifact", "inline_page_footer", "garbled_formula_token"} else "normal",
                    "target_type": "audit_issue",
                    "target_id": issue["id"],
                    "page_numbers": [],
                    "reason": f"{issue.get('issue_type')}: {issue.get('fragment')}",
                }
            )
    return queue


def build_review_markdown(evidence: Dict) -> str:
    document = evidence.get("document", {})
    queue = evidence.get("review_queue", [])
    lines = [
        "# PDF Evidence 复核队列",
        "",
        f"- 文档：{document.get('title') or document.get('id')}",
        f"- 版本：{document.get('version_label')}",
        f"- 规则类型：{document.get('rule_type')}",
        f"- 待复核项：{len(queue)}",
        "",
        "| 优先级 | 类型 | 对象 | 页码 | 原因 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in queue:
        pages = ",".join(str(page) for page in item.get("page_numbers") or [])
        reason = str(item.get("reason") or "").replace("\n", " ")
        lines.append(f"| {item.get('priority')} | {item.get('target_type')} | {item.get('target_id')} | {pages} | {reason} |")
    return "\n".join(lines).strip() + "\n"


def build_evidence(args: argparse.Namespace) -> int:
    structure_path = resolve_path(args.structure_json)
    report_path = resolve_path(args.report_json)
    source_pdf = resolve_path(args.source_pdf)
    raw_text_path = resolve_path(args.raw_text) if args.raw_text else None
    markdown_path = resolve_path(args.markdown) if args.markdown else None
    mineru_seed_path = resolve_path(args.mineru_seed_json) if args.mineru_seed_json else None
    output_json = resolve_path(args.output_json)
    output_review_md = resolve_path(args.output_review_md) if args.output_review_md else None

    if not structure_path or not structure_path.exists():
        raise SystemExit(f"Structure JSON does not exist: {structure_path}")
    if not report_path or not report_path.exists():
        raise SystemExit(f"Report JSON does not exist: {report_path}")
    if not source_pdf or not source_pdf.exists():
        raise SystemExit(f"Source PDF does not exist: {source_pdf}")
    if output_json is None:
        raise SystemExit("--output-json is required")

    print(f"Resolved source PDF: {source_pdf}")
    print(f"Resolved structure JSON: {structure_path}")
    print(f"Resolved report JSON: {report_path}")
    if raw_text_path:
        print(f"Resolved raw text: {raw_text_path}")
    if markdown_path:
        print(f"Resolved markdown: {markdown_path}")
    if mineru_seed_path:
        if not mineru_seed_path.exists():
            raise SystemExit(f"MinerU seed JSON does not exist: {mineru_seed_path}")
        print(f"Resolved MinerU seed JSON: {mineru_seed_path}")

    structure = read_json(structure_path)
    report = read_json(report_path)
    document = copy.deepcopy(structure.get("document", {}))
    document["source_sha256"] = sha256_file(source_pdf)
    if raw_text_path:
        document["raw_text_sha256"] = sha256_file(raw_text_path)
    document["structure_json_path"] = str(structure_path)
    document["structure_json_sha256"] = sha256_file(structure_path)
    if markdown_path:
        document["markdown_path"] = str(markdown_path)
        document["markdown_sha256"] = sha256_file(markdown_path)
    if mineru_seed_path:
        document["mineru_seed_json_path"] = str(mineru_seed_path)
        document["mineru_seed_json_sha256"] = sha256_file(mineru_seed_path)

    clauses, formula_candidates = build_clause_evidence(structure.get("clauses", []))
    appendices, table_candidates = build_appendix_evidence(structure.get("appendices", []))
    image_candidates: List[Dict] = []
    mineru_summary: Dict = {}
    if mineru_seed_path:
        mineru_seed = read_json(mineru_seed_path)
        mineru_seed["seed_json_path"] = str(mineru_seed_path)
        mineru_summary, mineru_formulas, mineru_tables, mineru_images = normalize_mineru_seed(mineru_seed)
        formula_candidates.extend(mineru_formulas)
        table_candidates.extend(mineru_tables)
        image_candidates.extend(mineru_images)

    evidence = {
        "schema_version": SCHEMA_VERSION,
        "created_at": now_iso(),
        "document": document,
        "extraction_run": {
            "raw_text_path": str(raw_text_path) if raw_text_path else document.get("raw_text_path"),
            "report_json_path": str(report_path),
            "structure_json_path": str(structure_path),
            "markdown_path": str(markdown_path) if markdown_path else None,
            "quality_summary": report.get("document_strategy") or structure.get("quality_summary"),
        },
        "pages": extract_page_blocks(source_pdf, report),
        "clauses": clauses,
        "appendices": appendices,
        "formula_candidates": formula_candidates,
        "table_candidates": table_candidates,
        "image_candidates": image_candidates,
        "mineru": mineru_summary,
        "audit_issues": build_audit_issues(markdown_path),
        "backfill_patches": [],
    }
    evidence["review_queue"] = build_review_queue(evidence)
    write_json(output_json, evidence)
    if output_review_md:
        output_review_md.parent.mkdir(parents=True, exist_ok=True)
        output_review_md.write_text(build_review_markdown(evidence), encoding="utf-8")
    print(f"Evidence JSON written: {output_json}")
    if output_review_md:
        print(f"Review queue written: {output_review_md}")
    print(f"Review queue count: {len(evidence['review_queue'])}")
    return 0


def iter_target_lists(evidence: Dict) -> Iterable[List[Dict]]:
    for key in ("formula_candidates", "table_candidates", "audit_issues", "clauses", "appendices", "pages"):
        value = evidence.get(key)
        if isinstance(value, list):
            yield value


def find_target(evidence: Dict, target_id: str) -> Optional[Dict]:
    for collection in iter_target_lists(evidence):
        for item in collection:
            if str(item.get("id")) == str(target_id) or str(item.get("page")) == str(target_id):
                return item
    return None


def apply_backfill_patch(args: argparse.Namespace) -> int:
    evidence_path = resolve_path(args.evidence_json)
    patch_path = resolve_path(args.patch_json)
    output_json = resolve_path(args.output_json) if args.output_json else evidence_path
    output_review_md = resolve_path(args.output_review_md) if args.output_review_md else None
    if not evidence_path or not evidence_path.exists():
        raise SystemExit(f"Evidence JSON does not exist: {evidence_path}")
    if not patch_path or not patch_path.exists():
        raise SystemExit(f"Patch JSON does not exist: {patch_path}")
    if output_json is None:
        raise SystemExit("--output-json is required when --evidence-json is empty")

    evidence = read_json(evidence_path)
    patch_payload = read_json(patch_path)
    patches = patch_payload.get("patches", [])
    if not isinstance(patches, list):
        raise SystemExit("Patch JSON must contain a list field: patches")

    applied: List[Dict] = []
    for patch in patches:
        target_id = patch.get("target_id")
        fields = patch.get("fields") or {}
        if not target_id or not isinstance(fields, dict):
            continue
        target = find_target(evidence, str(target_id))
        if target is None:
            applied.append({"target_id": target_id, "status": "missing_target"})
            continue
        before = {key: target.get(key) for key in fields}
        target.update(fields)
        applied.append(
            {
                "target_id": target_id,
                "status": "applied",
                "before": before,
                "after": {key: target.get(key) for key in fields},
                "note": patch.get("note"),
            }
        )

    evidence.setdefault("backfill_patches", []).append(
        {
            "applied_at": now_iso(),
            "patch_path": str(patch_path),
            "author": patch_payload.get("author") or args.author,
            "items": applied,
        }
    )
    evidence["review_queue"] = build_review_queue(evidence)
    write_json(output_json, evidence)
    if output_review_md:
        output_review_md.parent.mkdir(parents=True, exist_ok=True)
        output_review_md.write_text(build_review_markdown(evidence), encoding="utf-8")
    print(f"Evidence JSON written: {output_json}")
    print(f"Applied patches: {sum(1 for item in applied if item['status'] == 'applied')}")
    print(f"Review queue count: {len(evidence['review_queue'])}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build or patch policy-document evidence JSON")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build evidence JSON from PDF, report, structure JSON, and markdown")
    build_parser.add_argument("--source-pdf", required=True)
    build_parser.add_argument("--raw-text")
    build_parser.add_argument("--report-json", required=True)
    build_parser.add_argument("--structure-json", required=True)
    build_parser.add_argument("--markdown")
    build_parser.add_argument("--mineru-seed-json")
    build_parser.add_argument("--output-json", required=True)
    build_parser.add_argument("--output-review-md")
    build_parser.set_defaults(func=build_evidence)

    patch_parser = subparsers.add_parser("patch", help="Apply a backfill patch JSON to evidence")
    patch_parser.add_argument("--evidence-json", required=True)
    patch_parser.add_argument("--patch-json", required=True)
    patch_parser.add_argument("--output-json")
    patch_parser.add_argument("--output-review-md")
    patch_parser.add_argument("--author", default="manual")
    patch_parser.set_defaults(func=apply_backfill_patch)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
