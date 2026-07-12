#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build review packets for Codex/agent visual formula backfill.

API-based multimodal recognition can run fully inside scripts and needs an API
key. The Codex agent's own vision ability is a separate internal review path:
it can inspect local page images during a conversation without a workspace API
key, then write reviewed patches. This helper prepares small, ordered packets
with image paths, structure context, and patch templates so that agent-vision
work is traceable instead of ad hoc.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional


DEFAULT_TARGET_TYPES = {"formula_candidate", "table_candidate"}


def resolve_path(raw_path: str | Path | None) -> Optional[Path]:
    if not raw_path:
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def read_json(path: Path) -> Dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_preview(text: str, limit: int = 1400) -> str:
    cleaned = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "..."


def target_index(structure: Dict) -> Dict[str, Dict[str, Dict]]:
    return {
        "clause": {str(item.get("id")): item for item in structure.get("clauses", [])},
        "appendix": {str(item.get("id")): item for item in structure.get("appendices", [])},
    }


def candidate_index(evidence: Dict) -> Dict[str, Dict]:
    indexed: Dict[str, Dict] = {}
    for key in ("formula_candidates", "table_candidates"):
        for item in evidence.get(key, []) or []:
            indexed[str(item.get("id"))] = item
    return indexed


def default_image_dirs(evidence: Dict) -> List[Path]:
    document = evidence.get("document", {})
    document_id = document.get("id")
    if not document_id:
        return []
    return [
        resolve_path(f"tmp/pdfs/{document_id}_formula_review_tesseract"),
        resolve_path(f"tmp/pdfs/{document_id}_formula_review"),
        resolve_path(f"tmp/pdfs/{document_id}_appendix_review"),
    ]


def page_image_paths(page_numbers: Iterable[int], image_dirs: List[Path]) -> List[Path]:
    paths: List[Path] = []
    seen = set()
    for page_number in page_numbers:
        for image_dir in image_dirs:
            if not image_dir:
                continue
            candidate = image_dir / f"page_{int(page_number):03d}.png"
            if candidate.exists():
                normalized = str(candidate)
                if normalized not in seen:
                    seen.add(normalized)
                    paths.append(candidate)
    return paths


def selected_queue_items(evidence: Dict, max_items: int, target_types: set[str]) -> List[Dict]:
    items: List[Dict] = []
    priority_order = {"high": 0, "normal": 1, "low": 2}
    queue = evidence.get("review_queue", []) or []
    queue = sorted(
        queue,
        key=lambda item: (
            priority_order.get(str(item.get("priority") or ""), 9),
            min(item.get("page_numbers") or [999999]),
            str(item.get("target_id") or ""),
        ),
    )
    for item in queue:
        if item.get("target_type") not in target_types:
            continue
        items.append(item)
        if len(items) >= max_items:
            break
    return items


def chunked(items: List[Dict], batch_size: int) -> Iterable[List[Dict]]:
    for index in range(0, len(items), batch_size):
        yield items[index : index + batch_size]


def patch_template_for(candidate: Dict, target: Dict | None) -> Dict:
    owner_type = candidate.get("owner_type")
    owner_id = candidate.get("owner_id")
    return {
        "target_type": owner_type,
        "target_id": owner_id,
        "note": "Fill fields after visual review. Leave fields empty when unresolved.",
        "fields": {},
        "examples": {
            "formula_backfill": {
                "content_source": "agent_vision_formula_backfill",
                "content_review_required": False,
                "content_issues": [],
                "review_priority": "normal",
                "content_markdown_lines": ["TODO: reviewed Markdown with LaTeX"],
            },
            "no_formula_required": {
                "content_source": "agent_vision_no_formula_required",
                "content_review_required": False,
                "content_issues": [],
                "review_priority": "normal",
            },
            "still_unresolved": {
                "content_review_required": True,
                "content_issues": ["TODO: unresolved reason"],
                "review_priority": "high",
            },
        },
        "current_source": (target or {}).get("content_source"),
    }


def markdown_for_batch(
    evidence: Dict,
    structure: Dict,
    batch_items: List[Dict],
    image_dirs: List[Path],
    batch_number: int,
    patch_path: Path,
) -> str:
    candidates = candidate_index(evidence)
    targets = target_index(structure)
    document = evidence.get("document", {})
    lines = [
        "# Agent Vision Review Packet",
        "",
        f"- Document: {document.get('id') or ''}",
        f"- Title: {document.get('title') or ''}",
        f"- Batch: {batch_number}",
        f"- Patch template: {patch_path}",
        "",
        "## Review rules",
        "",
        "1. Use cached/API results first when available.",
        "2. Missing API credentials only disables script automation; it does not block Codex/GPT visual review.",
        "3. Inspect the listed page images directly and transcribe visible formulas/tables.",
        "4. If the page has a visible formula/table, transcribe only what is visible and mark unresolved parts explicitly.",
        "5. If the target is only a heading or plain text captured because it shares a formula page, mark it as no_formula_required.",
        "6. Write reviewed output into the patch template, then apply it with apply_structure_backfill.py.",
        "",
        "## Items",
        "",
    ]

    for item_number, queue_item in enumerate(batch_items, start=1):
        candidate = candidates.get(str(queue_item.get("target_id"))) or {}
        owner_type = str(candidate.get("owner_type") or "")
        owner_id = str(candidate.get("owner_id") or "")
        target = targets.get(owner_type, {}).get(owner_id, {})
        pages = queue_item.get("page_numbers") or candidate.get("page_numbers") or []
        images = page_image_paths(pages, image_dirs)

        lines.extend(
            [
                f"### Item {item_number}: {queue_item.get('target_id')}",
                "",
                f"- Priority: {queue_item.get('priority')}",
                f"- Target type: {owner_type}",
                f"- Target id: {owner_id}",
                f"- Pages: {', '.join(str(page) for page in pages)}",
                f"- Reason: {queue_item.get('reason')}",
                "- Images:",
            ]
        )
        if images:
            for image in images:
                lines.append(f"  - {image}")
        else:
            lines.append("  - MISSING: render or point --image-dir to page screenshots")

        current_text = target.get("content_markdown") or target.get("text") or target.get("content") or ""
        lines.extend(
            [
                "",
                "- Evidence preview:",
                "",
                "```text",
                safe_preview(candidate.get("text_preview") or ""),
                "```",
                "",
                "- Current structured content:",
                "",
                "```text",
                safe_preview(current_text),
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def build_packets(args: argparse.Namespace) -> int:
    evidence_path = resolve_path(args.evidence_json)
    if not evidence_path or not evidence_path.exists():
        raise SystemExit(f"Evidence JSON does not exist: {evidence_path}")
    evidence = read_json(evidence_path)

    structure_path = resolve_path(args.structure_json) if args.structure_json else resolve_path(
        evidence.get("document", {}).get("structure_json_path")
    )
    if not structure_path or not structure_path.exists():
        raise SystemExit(f"Structure JSON does not exist: {structure_path}")
    structure = read_json(structure_path)

    output_dir = resolve_path(args.output_dir)
    if output_dir is None:
        raise SystemExit("--output-dir is required")
    document_id = evidence.get("document", {}).get("id") or evidence_path.stem
    output_dir = output_dir / str(document_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    image_dirs = [resolve_path(path) for path in (args.image_dir or [])]
    if not image_dirs:
        image_dirs = default_image_dirs(evidence)
    image_dirs = [path for path in image_dirs if path]

    target_types = set(args.target_type or DEFAULT_TARGET_TYPES)
    items = selected_queue_items(evidence, args.max_items, target_types)
    candidates = candidate_index(evidence)
    targets = target_index(structure)

    packet_count = 0
    for batch_number, batch_items in enumerate(chunked(items, args.batch_size), start=1):
        patch_payload = {
            "author": "agent_vision_review",
            "evidence_json": str(evidence_path),
            "structure_json": str(structure_path),
            "patches": [],
        }
        for queue_item in batch_items:
            candidate = candidates.get(str(queue_item.get("target_id"))) or {}
            owner_type = str(candidate.get("owner_type") or "")
            owner_id = str(candidate.get("owner_id") or "")
            target = targets.get(owner_type, {}).get(owner_id)
            patch_payload["patches"].append(patch_template_for(candidate, target))

        patch_path = output_dir / f"batch_{batch_number:03d}_patch_template.json"
        packet_path = output_dir / f"batch_{batch_number:03d}.md"
        patch_path.write_text(json.dumps(patch_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        packet_path.write_text(
            markdown_for_batch(evidence, structure, batch_items, image_dirs, batch_number, patch_path),
            encoding="utf-8",
        )
        packet_count += 1
        print(f"Packet written: {packet_path}")
        print(f"Patch template written: {patch_path}")

    print(f"Selected review items: {len(items)}")
    print(f"Packet count: {packet_count}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Codex/agent visual review packets from Evidence queues.")
    parser.add_argument("--evidence-json", required=True)
    parser.add_argument("--structure-json")
    parser.add_argument("--output-dir", default="2_结构化产物/evidence/agent_vision_packets")
    parser.add_argument("--image-dir", action="append", help="Directory containing page_###.png images. Repeatable.")
    parser.add_argument("--target-type", action="append", choices=["formula_candidate", "table_candidate"])
    parser.add_argument("--max-items", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=5)
    return parser


def main() -> int:
    return build_packets(build_parser().parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
