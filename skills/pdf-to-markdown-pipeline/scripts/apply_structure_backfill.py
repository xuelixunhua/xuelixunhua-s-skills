#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Apply reviewed content backfills to structured JSON and regenerate Markdown.

This is the bridge from review/evidence work back to the final reusable
Markdown + JSON artifacts. Evidence/review files are not downstream inputs;
they drive patches that update the canonical structured outputs.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, Optional

from build_rule_structure import build_markdown


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def iter_targets(structured: Dict, target_type: str) -> Iterable[Dict]:
    if target_type == "clause":
        yield from structured.get("clauses", [])
    elif target_type == "appendix":
        yield from structured.get("appendices", [])
    else:
        raise ValueError(f"Unsupported target_type: {target_type}")


def find_target(structured: Dict, target_type: str, target_id: str) -> Optional[Dict]:
    for item in iter_targets(structured, target_type):
        if str(item.get("id")) == str(target_id):
            return item
    return None


def normalize_delivery_fields(structured: Dict) -> None:
    """Keep reusable JSON mirrors aligned with reviewed Markdown content."""
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


def apply_replacements(target: Dict, replacements: list[Dict]) -> int:
    applied = 0
    for replacement in replacements:
        field = replacement.get("field") or "content_markdown"
        text = str(target.get(field) or "")
        if not text:
            continue
        replacement_text = replacement.get("new")
        if "new_lines" in replacement:
            replacement_text = "\n".join(str(line) for line in replacement.get("new_lines") or [])
        new_text = text
        if replacement.get("old") is not None:
            new_text = text.replace(str(replacement["old"]), str(replacement_text or ""))
        elif replacement.get("old_regex") is not None:
            # Use a callable replacement so LaTeX backslashes such as \sum are
            # copied literally instead of being parsed as regex replacement escapes.
            new_text = re.sub(
                str(replacement["old_regex"]),
                lambda _match: str(replacement_text or ""),
                text,
                flags=re.S,
            )
        if new_text != text:
            target[field] = new_text
            applied += 1
    return applied


def apply_patch_payload(structured: Dict, payload: Dict) -> list[Dict]:
    results: list[Dict] = []
    for patch in payload.get("patches", []):
        target_type = patch.get("target_type")
        target_id = patch.get("target_id")
        if not target_type or not target_id:
            results.append({"target_id": target_id, "status": "invalid"})
            continue
        target = find_target(structured, str(target_type), str(target_id))
        if target is None:
            results.append({"target_id": target_id, "status": "missing"})
            continue
        old_content_markdown = target.get("content_markdown")
        fields = dict(patch.get("fields") or {})
        if "content_markdown_lines" in fields:
            fields["content_markdown"] = "\n".join(str(line) for line in fields.pop("content_markdown_lines"))
        if fields:
            target.update(fields)
            if "content_markdown" in fields:
                # The reusable JSON should not keep OCR-corrupted mirrors beside
                # the reviewed canonical markdown.
                target.pop("text_before_backfill", None)
                target.pop("default_markdown_before_backfill", None)
                target["text"] = fields["content_markdown"]
                target["default_markdown"] = fields["content_markdown"]
        replacement_count = apply_replacements(target, patch.get("replacements") or [])
        if replacement_count and target.get("content_markdown") != old_content_markdown:
            target.pop("text_before_backfill", None)
            target.pop("default_markdown_before_backfill", None)
            target["text"] = target.get("content_markdown")
            target["default_markdown"] = target.get("content_markdown")
        results.append({"target_id": target_id, "status": "applied", "replacement_count": replacement_count})
    normalize_delivery_fields(structured)
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply reviewed backfill patches to structured JSON")
    parser.add_argument("--structure-json", required=True)
    parser.add_argument("--patch-json", required=True)
    parser.add_argument("--output-json")
    parser.add_argument("--output-md")
    args = parser.parse_args()

    structure_path = resolve_path(args.structure_json)
    patch_path = resolve_path(args.patch_json)
    output_json = resolve_path(args.output_json) if args.output_json else structure_path
    output_md = resolve_path(args.output_md) if args.output_md else None

    structured = json.loads(structure_path.read_text(encoding="utf-8"))
    patch_payload = json.loads(patch_path.read_text(encoding="utf-8"))
    results = apply_patch_payload(structured, patch_payload)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(structured, ensure_ascii=False, indent=2), encoding="utf-8")
    if output_md:
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(build_markdown(structured), encoding="utf-8")

    print(f"Structure JSON written: {output_json}")
    if output_md:
        print(f"Markdown written: {output_md}")
    print(f"Applied patches: {sum(1 for item in results if item['status'] == 'applied')}")
    for item in results:
        print(f"- {item['target_id']}: {item['status']} replacements={item.get('replacement_count', 0)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
