#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a clause-level diff from two structured rule JSON files.

Goals:
1. identify added / removed / revised clauses
2. separate pure renumbering from material text change
3. provide a reusable JSON basis for formal difference reports
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


NOISE_BLOCK_RE = re.compile(r"\{\s*,\s*\d+[^{}]{0,40}?榰")
CLAUSE_PREFIX_RE = re.compile(r"^第[一二三四五六七八九十百零]+条(?:\s*\[[^\]]+\])?")
FORMULA_CONTEXT_RE = re.compile(r"(计算公式|具体公式|公式如下|公式为|分摊返还方式|求和|返还方式)")
FORMULA_SYMBOL_RE = re.compile(r"[=+\-*/%<>∑ΣΠπΔλβμ±÷×]")
SINGLE_LETTER_TOKEN_RE = re.compile(r"(?<![A-Za-z])[A-Za-z](?![A-Za-z])")
LATEX_BLOCK_RE = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)


def resolve_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def clean_text(text: str) -> str:
    text = NOISE_BLOCK_RE.sub(" ", text)
    text = text.replace("\x00", " ")
    text = text.replace("\u0098", " ")
    text = LATEX_BLOCK_RE.sub(lambda match: match.group(1), text)
    text = text.replace("$$", " ")
    text = text.replace("`", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    return text.strip()


def compare_text(text: str) -> str:
    text = clean_text(text)
    text = text.replace(" ", "")
    text = re.sub(r"[“”\"'`]", "", text)
    text = re.sub(r"[，。；：、（）()《》]", "", text)
    return text


def clause_body(text: str) -> str:
    text = clean_text(text)
    text = CLAUSE_PREFIX_RE.sub("", text).strip()
    return text


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
    compact = clean_text(text)
    score = formula_token_score(compact)
    if FORMULA_CONTEXT_RE.search(compact) and score >= 6:
        return True
    if score >= 18:
        return True
    if "）（）（" in compact or "" in compact or "" in compact:
        return True
    return False


def normalize_label(label: str) -> str:
    label = clean_text(label)
    label = re.sub(r"\s+", "", label)
    return label


def text_similarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, compare_text(clause_body(left)), compare_text(clause_body(right))).ratio()


def markdown_excerpt(text: str, limit: int = 360) -> str:
    excerpt = str(text or "").strip()
    excerpt = re.sub(r"\n{3,}", "\n\n", excerpt)
    if len(excerpt) > limit:
        excerpt = excerpt[: limit - 1].rstrip() + "…"
    if excerpt.count("$$") % 2 == 1:
        excerpt += "\n$$"
    return excerpt


def label_similarity(left: str, right: str) -> float:
    return difflib.SequenceMatcher(None, normalize_label(left), normalize_label(right)).ratio()


def chapter_lookup(structured: Dict) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for node in structured.get("section_nodes", []):
        if node["node_type"] == "chapter":
            result[node["id"]] = f"{node['marker']} {node['title']}"
    return result


def prepare_clauses(structured: Dict) -> List[Dict]:
    chapter_map = chapter_lookup(structured)
    occurrences: Dict[str, int] = {}
    prepared: List[Dict] = []

    for index, clause in enumerate(structured.get("clauses", []), start=1):
        display_markdown = clause.get("content_markdown") or clause["text"]
        norm_label = normalize_label(clause.get("label") or "")
        if norm_label:
            occurrences[norm_label] = occurrences.get(norm_label, 0) + 1
            occurrence_index = occurrences[norm_label]
        else:
            occurrence_index = 0
        prepared.append(
            {
                "order": index,
                "id": clause["id"],
                "marker": clause["marker"],
                "label": clause.get("label"),
                "normalized_label": norm_label,
                "text": clause["text"],
                "display_markdown": display_markdown,
                "clean_text": clean_text(display_markdown),
                "body_text": clause_body(display_markdown),
                "compare_text": compare_text(clause_body(display_markdown)),
                "chapter_title": chapter_map.get(clause.get("chapter_id") or "", ""),
                "occurrence_index": occurrence_index,
                "formula_sensitive": clause.get("formula_sensitive", False)
                or looks_formula_sensitive_text(display_markdown),
            }
        )
    return prepared


def direct_match(old_clauses: List[Dict], new_clauses: List[Dict]) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    old_groups: Dict[str, List[int]] = {}
    new_groups: Dict[str, List[int]] = {}

    for idx, clause in enumerate(old_clauses):
        if clause["normalized_label"]:
            old_groups.setdefault(clause["normalized_label"], []).append(idx)
    for idx, clause in enumerate(new_clauses):
        if clause["normalized_label"]:
            new_groups.setdefault(clause["normalized_label"], []).append(idx)

    matches: List[Tuple[int, int]] = []
    matched_old: set[int] = set()
    matched_new: set[int] = set()

    for label in sorted(set(old_groups) & set(new_groups)):
        old_indexes = old_groups[label]
        new_indexes = new_groups[label]
        if len(old_indexes) == len(new_indexes):
            for old_idx, new_idx in zip(old_indexes, new_indexes):
                matches.append((old_idx, new_idx))
                matched_old.add(old_idx)
                matched_new.add(new_idx)

    unmatched_old = [idx for idx in range(len(old_clauses)) if idx not in matched_old]
    unmatched_new = [idx for idx in range(len(new_clauses)) if idx not in matched_new]
    return matches, unmatched_old, unmatched_new


def fuzzy_match(
    old_clauses: List[Dict],
    new_clauses: List[Dict],
    unmatched_old: List[int],
    unmatched_new: List[int],
) -> List[Tuple[int, int, float]]:
    candidates: List[Tuple[float, int, int]] = []
    for old_idx in unmatched_old:
        old_clause = old_clauses[old_idx]
        for new_idx in unmatched_new:
            new_clause = new_clauses[new_idx]
            label_score = label_similarity(old_clause["label"] or "", new_clause["label"] or "")
            text_score = text_similarity(old_clause["display_markdown"], new_clause["display_markdown"])
            chapter_bonus = 0.05 if old_clause["chapter_title"] == new_clause["chapter_title"] else 0.0
            score = label_score * 0.55 + text_score * 0.45 + chapter_bonus
            if max(label_score, text_score) >= 0.60 and score >= 0.68:
                candidates.append((score, old_idx, new_idx))

    candidates.sort(reverse=True)
    results: List[Tuple[int, int, float]] = []
    used_old: set[int] = set()
    used_new: set[int] = set()

    for score, old_idx, new_idx in candidates:
        if old_idx in used_old or new_idx in used_new:
            continue
        used_old.add(old_idx)
        used_new.add(new_idx)
        results.append((old_idx, new_idx, round(score, 4)))

    return results


def classify_matches(
    old_clauses: List[Dict],
    new_clauses: List[Dict],
    direct_matches: List[Tuple[int, int]],
    fuzzy_matches: List[Tuple[int, int, float]],
) -> Dict:
    matched_old = {old_idx for old_idx, _ in direct_matches}
    matched_new = {new_idx for _, new_idx in direct_matches}
    matched_old.update(old_idx for old_idx, _, _ in fuzzy_matches)
    matched_new.update(new_idx for _, new_idx, _ in fuzzy_matches)

    unchanged: List[Dict] = []
    renumbered: List[Dict] = []
    revised: List[Dict] = []

    for old_idx, new_idx in direct_matches:
        old_clause = old_clauses[old_idx]
        new_clause = new_clauses[new_idx]
        similarity = round(text_similarity(old_clause["display_markdown"], new_clause["display_markdown"]), 4)
        payload = {
            "old_marker": old_clause["marker"],
            "new_marker": new_clause["marker"],
            "label": new_clause["label"] or old_clause["label"],
            "chapter_title": new_clause["chapter_title"] or old_clause["chapter_title"],
            "similarity": similarity,
            "old_text": old_clause["body_text"],
            "new_text": new_clause["body_text"],
            "old_markdown": old_clause["display_markdown"],
            "new_markdown": new_clause["display_markdown"],
            "formula_sensitive": old_clause["formula_sensitive"] or new_clause["formula_sensitive"],
        }
        if old_clause["compare_text"] == new_clause["compare_text"]:
            if old_clause["marker"] == new_clause["marker"]:
                unchanged.append(payload)
            else:
                renumbered.append(payload)
        else:
            revised.append(payload)

    for old_idx, new_idx, score in fuzzy_matches:
        old_clause = old_clauses[old_idx]
        new_clause = new_clauses[new_idx]
        payload = {
            "old_marker": old_clause["marker"],
            "new_marker": new_clause["marker"],
            "label": new_clause["label"] or old_clause["label"],
            "chapter_title": new_clause["chapter_title"] or old_clause["chapter_title"],
            "similarity": round(text_similarity(old_clause["display_markdown"], new_clause["display_markdown"]), 4),
            "match_score": score,
            "old_text": old_clause["body_text"],
            "new_text": new_clause["body_text"],
            "old_markdown": old_clause["display_markdown"],
            "new_markdown": new_clause["display_markdown"],
            "formula_sensitive": old_clause["formula_sensitive"] or new_clause["formula_sensitive"],
        }
        if old_clause["compare_text"] == new_clause["compare_text"]:
            if old_clause["marker"] == new_clause["marker"]:
                unchanged.append(payload)
            else:
                renumbered.append(payload)
        else:
            revised.append(payload)

    added = [
        {
            "marker": clause["marker"],
            "label": clause["label"],
            "chapter_title": clause["chapter_title"],
            "text": clause["clean_text"],
            "markdown": clause["display_markdown"],
            "formula_sensitive": clause["formula_sensitive"],
        }
        for idx, clause in enumerate(new_clauses)
        if idx not in matched_new
    ]
    removed = [
        {
            "marker": clause["marker"],
            "label": clause["label"],
            "chapter_title": clause["chapter_title"],
            "text": clause["clean_text"],
            "markdown": clause["display_markdown"],
            "formula_sensitive": clause["formula_sensitive"],
        }
        for idx, clause in enumerate(old_clauses)
        if idx not in matched_old
    ]

    revised.sort(key=lambda item: item["similarity"])
    return {
        "unchanged": unchanged,
        "renumbered": renumbered,
        "revised": revised,
        "added": added,
        "removed": removed,
    }


def build_markdown(diff: Dict) -> str:
    summary = diff["summary"]
    lines = [
        "# 条款差异样板",
        "",
        "## 摘要",
        f"- 旧版本条款数：`{summary['old_clause_count']}`",
        f"- 新版本条款数：`{summary['new_clause_count']}`",
        f"- 新增条款：`{summary['added_count']}`",
        f"- 删除条款：`{summary['removed_count']}`",
        f"- 改写条款：`{summary['revised_count']}`",
        f"- 仅条号顺移：`{summary['renumbered_count']}`",
        "",
        "## 重点改写条款",
    ]

    if diff["revised_clauses"]:
        for item in diff["revised_clauses"][:20]:
            lines.append(f"### {item['old_marker']} -> {item['new_marker']} {item['label'] or ''}".rstrip())
            lines.append(f"- 所属章节：`{item['chapter_title']}`")
            lines.append(f"- 相似度：`{item['similarity']}`")
            if item.get("formula_sensitive"):
                lines.append("- 提示：该条款包含复杂公式或计算表达，优先核对下面的条款 Markdown 与公式差异页。")
                if item.get("old_markdown"):
                    lines.append(f"- 旧版 Markdown：{markdown_excerpt(item['old_markdown'])}")
                if item.get("new_markdown"):
                    lines.append(f"- 新版 Markdown：{markdown_excerpt(item['new_markdown'])}")
                if not item.get("old_markdown") and not item.get("new_markdown"):
                    lines.append("- 说明：当前尚未回填可复用的公式 Markdown。")
            else:
                lines.append(f"- 旧文本：{item['old_text'][:260]}")
                lines.append(f"- 新文本：{item['new_text'][:260]}")
            lines.append("")
    else:
        lines.append("- 无")
        lines.append("")

    lines.append("## 新增条款")
    if diff["added_clauses"]:
        for item in diff["added_clauses"]:
            label = item["label"] or ""
            lines.append(f"- `{item['marker']}` {label} | `{item['chapter_title']}`")
    else:
        lines.append("- 无")
    lines.append("")

    lines.append("## 删除条款")
    if diff["removed_clauses"]:
        for item in diff["removed_clauses"]:
            label = item["label"] or ""
            lines.append(f"- `{item['marker']}` {label} | `{item['chapter_title']}`")
    else:
        lines.append("- 无")
    lines.append("")

    lines.append("## 条号顺移")
    if diff["renumbered_clauses"]:
        for item in diff["renumbered_clauses"][:30]:
            lines.append(f"- `{item['old_marker']} -> {item['new_marker']}` {item['label'] or ''}")
    else:
        lines.append("- 无")
    lines.append("")
    return "\n".join(lines).strip() + "\n"


def build_diff(old_structured: Dict, new_structured: Dict) -> Dict:
    old_clauses = prepare_clauses(old_structured)
    new_clauses = prepare_clauses(new_structured)

    direct_matches, unmatched_old, unmatched_new = direct_match(old_clauses, new_clauses)
    fuzzy_matches = fuzzy_match(old_clauses, new_clauses, unmatched_old, unmatched_new)
    classified = classify_matches(old_clauses, new_clauses, direct_matches, fuzzy_matches)

    return {
        "old_document": old_structured["document"],
        "new_document": new_structured["document"],
        "summary": {
            "old_clause_count": len(old_clauses),
            "new_clause_count": len(new_clauses),
            "added_count": len(classified["added"]),
            "removed_count": len(classified["removed"]),
            "revised_count": len(classified["revised"]),
            "renumbered_count": len(classified["renumbered"]),
            "unchanged_count": len(classified["unchanged"]),
        },
        "revised_clauses": classified["revised"],
        "added_clauses": classified["added"],
        "removed_clauses": classified["removed"],
        "renumbered_clauses": classified["renumbered"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build clause-level diff from structured JSON")
    parser.add_argument("--old", required=True, help="Old structured JSON path")
    parser.add_argument("--new", required=True, help="New structured JSON path")
    parser.add_argument("--output-json", required=True, help="Clause diff JSON output path")
    parser.add_argument("--output-md", help="Optional markdown summary output path")
    args = parser.parse_args()

    old_path = resolve_path(args.old)
    new_path = resolve_path(args.new)
    output_json = resolve_path(args.output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)

    old_structured = json.loads(old_path.read_text(encoding="utf-8"))
    new_structured = json.loads(new_path.read_text(encoding="utf-8"))
    diff = build_diff(old_structured, new_structured)

    output_json.write_text(json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Resolved old structured JSON: {old_path}")
    print(f"Resolved new structured JSON: {new_path}")
    print(f"Clause diff JSON written: {output_json}")

    if args.output_md:
        output_md = resolve_path(args.output_md)
        output_md.parent.mkdir(parents=True, exist_ok=True)
        output_md.write_text(build_markdown(diff), encoding="utf-8")
        print(f"Clause diff Markdown written: {output_md}")

    print(
        "Summary: "
        f"added={diff['summary']['added_count']}, "
        f"removed={diff['summary']['removed_count']}, "
        f"revised={diff['summary']['revised_count']}, "
        f"renumbered={diff['summary']['renumbered_count']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
