#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluate MinerU outputs and build a lightweight evidence seed.

This script is intentionally read-only against canonical project artifacts.
It consumes a MinerU `auto/` output directory and writes evaluation files under
the caller-provided output directory.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


FORMULA_BLOCK_RE = re.compile(r"\$\$(.*?)\$\$", re.S)
IMAGE_REF_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
SUSPICIOUS_LATEX_RE = re.compile(
    r"(\\#|\\sharp|\\breve|\\ddot|\\not\s|\\mathbb|☉|♯|#|\\\\s+_)"
)


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def find_one(directory: Path, suffix: str) -> Path | None:
    matches = sorted(directory.glob(f"*{suffix}"))
    return matches[0] if matches else None


def preview(text: str, limit: int = 240) -> str:
    cleaned = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "..."


def text_of(item: dict[str, Any]) -> str:
    return str(item.get("text") or item.get("html") or "")


def build_summary(auto_dir: Path, page_offset: int) -> tuple[dict[str, Any], dict[str, Any]]:
    content_list_path = find_one(auto_dir, "_content_list.json")
    content_list_v2_path = find_one(auto_dir, "_content_list_v2.json")
    markdown_path = find_one(auto_dir, ".md")
    middle_path = find_one(auto_dir, "_middle.json")
    model_path = find_one(auto_dir, "_model.json")
    layout_pdf = find_one(auto_dir, "_layout.pdf")
    span_pdf = find_one(auto_dir, "_span.pdf")

    if content_list_path is None:
        raise SystemExit(f"MinerU content_list not found in: {auto_dir}")

    items = read_json(content_list_path)
    if not isinstance(items, list):
        raise SystemExit(f"MinerU content_list is not a list: {content_list_path}")

    markdown = markdown_path.read_text(encoding="utf-8") if markdown_path and markdown_path.exists() else ""
    image_dir = auto_dir / "images"
    image_files = sorted(image_dir.glob("*")) if image_dir.exists() else []

    type_counts = Counter(str(item.get("type") or "unknown") for item in items)
    pages = sorted({int(item["page_idx"]) for item in items if isinstance(item.get("page_idx"), int)})
    page_counts: dict[int, Counter[str]] = defaultdict(Counter)
    bbox_count = 0
    for item in items:
        local_page = item.get("page_idx")
        if isinstance(local_page, int):
            page_counts[local_page + page_offset][str(item.get("type") or "unknown")] += 1
        if isinstance(item.get("bbox"), list) and len(item["bbox"]) == 4:
            bbox_count += 1

    equations = [item for item in items if item.get("type") == "equation"]
    tables = [item for item in items if item.get("type") == "table"]
    images = [item for item in items if item.get("type") == "image"]
    suspicious_equations = [
        {
            "page": int(item.get("page_idx", -1)) + page_offset,
            "bbox": item.get("bbox"),
            "preview": preview(text_of(item), 360),
        }
        for item in equations
        if SUSPICIOUS_LATEX_RE.search(text_of(item))
    ]

    formula_blocks = FORMULA_BLOCK_RE.findall(markdown)
    suspicious_formula_blocks = [block for block in formula_blocks if SUSPICIOUS_LATEX_RE.search(block)]

    summary = {
        "schema_version": "mineru_eval.v1",
        "auto_dir": str(auto_dir),
        "page_offset": page_offset,
        "artifacts": {
            "content_list": str(content_list_path),
            "content_list_v2": str(content_list_v2_path) if content_list_v2_path else None,
            "markdown": str(markdown_path) if markdown_path else None,
            "middle_json": str(middle_path) if middle_path else None,
            "model_json": str(model_path) if model_path else None,
            "layout_pdf": str(layout_pdf) if layout_pdf else None,
            "span_pdf": str(span_pdf) if span_pdf else None,
            "image_dir": str(image_dir) if image_dir.exists() else None,
        },
        "counts": {
            "content_items": len(items),
            "type_counts": dict(sorted(type_counts.items())),
            "pages_local": pages,
            "pages_physical_estimated": [page + page_offset for page in pages],
            "bbox_items": bbox_count,
            "image_files": len(image_files),
            "image_bytes": sum(path.stat().st_size for path in image_files if path.is_file()),
            "markdown_chars": len(markdown),
            "markdown_headings": sum(1 for line in markdown.splitlines() if line.startswith("#")),
            "markdown_formula_blocks": len(formula_blocks),
            "markdown_image_refs": len(IMAGE_REF_RE.findall(markdown)),
        },
        "quality_signals": {
            "equation_items": len(equations),
            "equation_items_with_suspicious_latex": len(suspicious_equations),
            "markdown_formula_blocks_with_suspicious_latex": len(suspicious_formula_blocks),
            "table_items": len(tables),
            "image_items": len(images),
            "page_number_items": type_counts.get("page_number", 0),
        },
        "page_type_counts": {
            str(page): dict(sorted(counter.items())) for page, counter in sorted(page_counts.items())
        },
        "examples": {
            "suspicious_equations": suspicious_equations[:8],
            "equations": [
                {
                    "page": int(item.get("page_idx", -1)) + page_offset,
                    "bbox": item.get("bbox"),
                    "preview": preview(text_of(item), 260),
                }
                for item in equations[:8]
            ],
            "tables": [
                {
                    "page": int(item.get("page_idx", -1)) + page_offset,
                    "bbox": item.get("bbox"),
                    "preview": preview(text_of(item), 260),
                }
                for item in tables[:4]
            ],
        },
    }

    seed_blocks: list[dict[str, Any]] = []
    formula_candidates: list[dict[str, Any]] = []
    table_candidates: list[dict[str, Any]] = []
    image_candidates: list[dict[str, Any]] = []
    for index, item in enumerate(items, start=1):
        item_type = str(item.get("type") or "unknown")
        local_page = item.get("page_idx")
        physical_page = local_page + page_offset if isinstance(local_page, int) else None
        block = {
            "id": f"mineru-block-{index:05d}",
            "source": "mineru_content_list",
            "type": item_type,
            "page_idx": local_page,
            "physical_page_estimated": physical_page,
            "bbox": item.get("bbox"),
            "text": text_of(item),
            "text_preview": preview(text_of(item)),
            "raw": item,
        }
        seed_blocks.append(block)
        if item_type == "equation":
            formula_candidates.append(
                {
                    "id": f"mineru-formula-{len(formula_candidates) + 1:05d}",
                    "block_id": block["id"],
                    "page": physical_page,
                    "bbox": item.get("bbox"),
                    "latex": text_of(item),
                    "img_path": item.get("img_path"),
                    "review_required": bool(SUSPICIOUS_LATEX_RE.search(text_of(item))),
                    "issues": ["suspicious_latex_tokens"] if SUSPICIOUS_LATEX_RE.search(text_of(item)) else [],
                }
            )
        elif item_type == "table":
            table_candidates.append(
                {
                    "id": f"mineru-table-{len(table_candidates) + 1:05d}",
                    "block_id": block["id"],
                    "page": physical_page,
                    "bbox": item.get("bbox"),
                    "html": text_of(item),
                    "img_path": item.get("img_path"),
                    "review_required": True,
                    "issues": ["table_structure_needs_business_review"],
                }
            )
        elif item_type == "image":
            image_candidates.append(
                {
                    "id": f"mineru-image-{len(image_candidates) + 1:05d}",
                    "block_id": block["id"],
                    "page": physical_page,
                    "bbox": item.get("bbox"),
                    "img_path": item.get("img_path"),
                    "review_required": True,
                    "issues": ["image_content_needs_review"],
                }
            )

    seed = {
        "schema_version": "mineru_evidence_seed.v1",
        "auto_dir": str(auto_dir),
        "page_offset": page_offset,
        "artifacts": summary["artifacts"],
        "blocks": seed_blocks,
        "formula_candidates": formula_candidates,
        "table_candidates": table_candidates,
        "image_candidates": image_candidates,
    }
    return summary, seed


def render_markdown(summary: dict[str, Any]) -> str:
    counts = summary["counts"]
    quality = summary["quality_signals"]
    artifacts = summary["artifacts"]
    lines = [
        "# MinerU Output Evaluation",
        "",
        f"- Auto dir: `{summary['auto_dir']}`",
        f"- Page offset: `{summary['page_offset']}`",
        f"- Content items: `{counts['content_items']}`",
        f"- Type counts: `{counts['type_counts']}`",
        f"- Estimated physical pages: `{counts['pages_physical_estimated']}`",
        f"- Markdown chars: `{counts['markdown_chars']}`",
        f"- Markdown headings: `{counts['markdown_headings']}`",
        f"- Markdown formula blocks: `{counts['markdown_formula_blocks']}`",
        f"- Equation items: `{quality['equation_items']}`",
        f"- Suspicious equation items: `{quality['equation_items_with_suspicious_latex']}`",
        f"- Table items: `{quality['table_items']}`",
        f"- Image items: `{quality['image_items']}`",
        f"- Page number items: `{quality['page_number_items']}`",
        "",
        "## Artifacts",
        "",
    ]
    for key, value in artifacts.items():
        lines.append(f"- `{key}`: `{value}`")

    lines.extend(["", "## Page Type Counts", ""])
    for page, counter in summary["page_type_counts"].items():
        lines.append(f"- Page `{page}`: `{counter}`")

    lines.extend(["", "## Suspicious Formula Examples", ""])
    examples = summary["examples"].get("suspicious_equations") or []
    if not examples:
        lines.append("- None")
    for item in examples:
        lines.append(f"- Page `{item['page']}`, bbox `{item.get('bbox')}`: {item['preview']}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a MinerU auto output directory")
    parser.add_argument("--auto-dir", required=True, help="MinerU output auto directory")
    parser.add_argument("--out-dir", required=True, help="Directory for evaluation output")
    parser.add_argument("--name", required=True, help="Output file prefix")
    parser.add_argument("--page-offset", type=int, default=0, help="Add to MinerU local page_idx")
    args = parser.parse_args()

    auto_dir = resolve_path(args.auto_dir)
    out_dir = resolve_path(args.out_dir)
    summary, seed = build_summary(auto_dir=auto_dir, page_offset=args.page_offset)

    summary_path = out_dir / f"{args.name}_mineru_eval.json"
    seed_path = out_dir / f"{args.name}_mineru_seed.json"
    markdown_path = out_dir / f"{args.name}_mineru_eval.md"
    write_json(summary_path, summary)
    write_json(seed_path, seed)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(render_markdown(summary), encoding="utf-8")

    print(f"Summary JSON written: {summary_path}")
    print(f"Evidence seed JSON written: {seed_path}")
    print(f"Markdown report written: {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
