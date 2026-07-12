#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run the shared PDF -> structured artifact gate.

This wrapper is intentionally narrow:
1. extract raw text and page-quality report
2. build structure JSON / Markdown
3. build Evidence JSON / review queue
4. run strict delivery audit before downstream analysis

By default the command fails when strict audit finds any issue. Use
--allow-findings only for draft runs where downstream outputs must be clearly
marked as non-delivery artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional


SCRIPT_DIR = Path(__file__).resolve().parent


@dataclass
class PipelineItem:
    document_id: str
    version_label: str
    rule_type: str
    pdf_path: Path


def resolve_path(raw_path: str | Path) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_file_stem(value: str) -> str:
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(value or "")).strip("._")
    return stem or "document"


def read_manifest(path: Path) -> List[PipelineItem]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    records = payload.get("documents") if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise SystemExit("Manifest must be a JSON list or an object with a documents list.")

    items: List[PipelineItem] = []
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise SystemExit(f"Manifest item {index} is not an object.")
        missing = [
            key
            for key in ("document_id", "version_label", "rule_type", "pdf_path")
            if not record.get(key)
        ]
        if missing:
            raise SystemExit(f"Manifest item {index} missing fields: {', '.join(missing)}")
        items.append(
            PipelineItem(
                document_id=str(record["document_id"]),
                version_label=str(record["version_label"]),
                rule_type=str(record["rule_type"]),
                pdf_path=resolve_path(str(record["pdf_path"])),
            )
        )
    return items


def build_items(args: argparse.Namespace) -> List[PipelineItem]:
    items: List[PipelineItem] = []
    if args.manifest:
        items.extend(read_manifest(resolve_path(args.manifest)))

    if args.pdf:
        missing = [
            name
            for name, value in (
                ("--document-id", args.document_id),
                ("--version-label", args.version_label),
                ("--rule-type", args.rule_type),
            )
            if not value
        ]
        if missing:
            raise SystemExit(f"Single PDF mode requires: {', '.join(missing)}")
        items.append(
            PipelineItem(
                document_id=args.document_id,
                version_label=args.version_label,
                rule_type=args.rule_type,
                pdf_path=resolve_path(args.pdf),
            )
        )

    if not items:
        raise SystemExit("Pass either --manifest or --pdf with document metadata.")
    return items


def output_paths(item: PipelineItem, args: argparse.Namespace) -> Dict[str, Path]:
    raw_dir = resolve_path(args.raw_text_dir)
    json_dir = resolve_path(args.json_dir)
    markdown_dir = resolve_path(args.markdown_dir)
    evidence_dir = resolve_path(args.evidence_dir)
    stem = item.document_id
    if args.extraction_engine == "mineru":
        raw_text_name = f"{stem}_mineru_raw.txt"
        report_name = f"{stem}_mineru_report.json"
    else:
        raw_text_name = f"{stem}_raw.txt"
        report_name = f"{stem}_report.json"
    return {
        "raw_text": raw_dir / raw_text_name,
        "report_json": raw_dir / report_name,
        "structure_json": json_dir / f"{stem}.json",
        "markdown": markdown_dir / f"{stem}.md",
        "evidence_json": evidence_dir / f"{stem}_evidence.json",
        "review_queue": evidence_dir / f"{stem}_review_queue.md",
        "mineru_manifest": raw_dir / f"{stem}_mineru_manifest.json",
        "mineru_seed_json": evidence_dir / f"{stem}_mineru_seed.json",
    }


def run_command(command: List[str], dry_run: bool = False, allow_failure: bool = False) -> int:
    print("Command:", subprocess.list2cmdline(command))
    if dry_run:
        return 0
    result = subprocess.run(command, cwd=str(Path.cwd()))
    if result.returncode and not allow_failure:
        raise SystemExit(result.returncode)
    return result.returncode


def ensure_parent_dirs(paths: Iterable[Path]) -> None:
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def run_pypdf_extraction(item: PipelineItem, args: argparse.Namespace, paths: Dict[str, Path]) -> None:
    run_command(
        [
            sys.executable,
            str(SCRIPT_DIR / "pdf_toolkit.py"),
            "extract",
            "--input",
            str(item.pdf_path),
            "--output-text",
            str(paths["raw_text"]),
            "--output-json",
            str(paths["report_json"]),
        ],
        dry_run=args.dry_run,
    )


def mineru_output_root(item: PipelineItem, args: argparse.Namespace) -> Path:
    return resolve_path(args.mineru_output_root) / item.document_id


def prepare_mineru_input(item: PipelineItem, args: argparse.Namespace) -> Path:
    if args.no_mineru_safe_copy:
        return item.pdf_path

    safe_dir = resolve_path(args.mineru_safe_input_dir)
    safe_dir.mkdir(parents=True, exist_ok=True)
    suffix = item.pdf_path.suffix if item.pdf_path.suffix else ".pdf"
    safe_path = safe_dir / f"{safe_file_stem(item.document_id)}{suffix.lower()}"
    if args.dry_run:
        print(f"Resolved MinerU runtime input: {safe_path}")
        return safe_path
    should_copy = True
    if safe_path.exists():
        source_stat = item.pdf_path.stat()
        target_stat = safe_path.stat()
        should_copy = (
            source_stat.st_size != target_stat.st_size
            or source_stat.st_mtime > target_stat.st_mtime + 1
        )
    if should_copy:
        shutil.copy2(item.pdf_path, safe_path)
    print(f"Resolved MinerU runtime input: {safe_path}")
    return safe_path


def infer_mineru_auto_dir(
    item: PipelineItem,
    args: argparse.Namespace,
    paths: Dict[str, Path],
    mineru_input_pdf: Path,
) -> Path:
    if paths["mineru_manifest"].exists():
        manifest = json.loads(paths["mineru_manifest"].read_text(encoding="utf-8"))
        auto_dir = manifest.get("auto_dir")
        if auto_dir:
            return resolve_path(auto_dir)
    base_dir = mineru_output_root(item, args) / mineru_input_pdf.stem
    for method_dir in ("auto", "ocr"):
        candidate = base_dir / method_dir
        if mineru_auto_dir_ready(candidate):
            return candidate
    return base_dir / "auto"


def mineru_auto_dir_ready(auto_dir: Path) -> bool:
    return auto_dir.exists() and bool(list(auto_dir.glob("*_content_list.json")))


def run_mineru_extraction(item: PipelineItem, args: argparse.Namespace, paths: Dict[str, Path]) -> None:
    mineru_input_pdf = prepare_mineru_input(item, args)
    output_root = mineru_output_root(item, args)
    inferred_auto_dir = infer_mineru_auto_dir(item, args, paths, mineru_input_pdf)
    if args.reuse_mineru_output and mineru_auto_dir_ready(inferred_auto_dir):
        print(f"Reusing MinerU auto dir: {inferred_auto_dir}")
    else:
        command = [
            sys.executable,
            str(SCRIPT_DIR / "run_mineru_local.py"),
            "--input-pdf",
            str(mineru_input_pdf),
            "--output-root",
            str(output_root),
            "--manifest-json",
            str(paths["mineru_manifest"]),
            "--mineru-command",
            args.mineru_command,
            "--backend",
            args.mineru_backend,
            "--method",
            args.mineru_method,
            "--lang",
            args.mineru_lang,
            "--model-source",
            args.mineru_model_source,
            "--formula",
            bool_text(not args.disable_mineru_formula),
            "--table",
            bool_text(not args.disable_mineru_table),
        ]
        if args.mineru_api_url:
            command.extend(["--api-url", args.mineru_api_url])
        if args.mineru_start_page is not None:
            command.extend(["--start-page", str(args.mineru_start_page)])
        if args.mineru_end_page is not None:
            command.extend(["--end-page", str(args.mineru_end_page)])
        run_command(command, dry_run=args.dry_run)

    auto_dir = infer_mineru_auto_dir(item, args, paths, mineru_input_pdf)
    first_page_number = (args.mineru_start_page + 1) if args.mineru_start_page is not None else 1
    command = [
        sys.executable,
        str(SCRIPT_DIR / "mineru_adapter.py"),
        "--auto-dir",
        str(auto_dir),
        "--source-pdf",
        str(item.pdf_path),
        "--first-page-number",
        str(first_page_number),
        "--output-raw-text",
        str(paths["raw_text"]),
        "--output-report-json",
        str(paths["report_json"]),
        "--output-seed-json",
        str(paths["mineru_seed_json"]),
    ]
    run_command(command, dry_run=args.dry_run)


def run_item(item: PipelineItem, args: argparse.Namespace) -> Dict[str, Path]:
    paths = output_paths(item, args)
    ensure_parent_dirs(paths.values())

    print("")
    print(f"Document id: {item.document_id}")
    print(f"Resolved PDF: {item.pdf_path}")
    for label, path in paths.items():
        print(f"Resolved {label}: {path}")

    if not item.pdf_path.exists():
        raise SystemExit(f"PDF does not exist: {item.pdf_path}")

    python = sys.executable
    if args.extraction_engine == "mineru":
        run_mineru_extraction(item, args, paths)
    else:
        run_pypdf_extraction(item, args, paths)

    structure_command = [
        python,
        str(SCRIPT_DIR / "build_rule_structure.py"),
        "--raw-text",
        str(paths["raw_text"]),
        "--report-json",
        str(paths["report_json"]),
        "--source-pdf",
        str(item.pdf_path),
        "--document-id",
        item.document_id,
        "--version-label",
        item.version_label,
        "--rule-type",
        item.rule_type,
        "--output-json",
        str(paths["structure_json"]),
        "--output-md",
        str(paths["markdown"]),
    ]
    if args.include_review_notes:
        structure_command.append("--include-review-notes")
    if args.enable_formula_markdown:
        structure_command.append("--enable-formula-markdown")
    if args.enable_appendix_markdown:
        structure_command.append("--enable-appendix-markdown")
    run_command(structure_command, dry_run=args.dry_run)

    run_command(
        [
            python,
            str(SCRIPT_DIR / "document_evidence.py"),
            "build",
            "--source-pdf",
            str(item.pdf_path),
            "--raw-text",
            str(paths["raw_text"]),
            "--report-json",
            str(paths["report_json"]),
            "--structure-json",
            str(paths["structure_json"]),
            "--markdown",
            str(paths["markdown"]),
            "--output-json",
            str(paths["evidence_json"]),
            "--output-review-md",
            str(paths["review_queue"]),
        ]
        + (
            ["--mineru-seed-json", str(paths["mineru_seed_json"])]
            if args.extraction_engine == "mineru"
            else []
        ),
        dry_run=args.dry_run,
    )
    return paths


def run_audit(items_paths: List[Dict[str, Path]], args: argparse.Namespace) -> None:
    evidence_dir = resolve_path(args.evidence_dir)
    audit_json = resolve_path(args.audit_output_json) if args.audit_output_json else evidence_dir / "strict_delivery_audit.json"
    audit_md = resolve_path(args.audit_output_md) if args.audit_output_md else evidence_dir / "strict_delivery_audit.md"
    ensure_parent_dirs([audit_json, audit_md])

    command = [
        sys.executable,
        str(SCRIPT_DIR / "audit_markdown_formula.py"),
        "--strict-delivery",
        "--output-json",
        str(audit_json),
        "--output-md",
        str(audit_md),
    ]
    for paths in items_paths:
        command.extend(["--input", str(paths["structure_json"])])
        command.extend(["--input", str(paths["markdown"])])
    if not args.allow_findings:
        command.append("--fail-on-findings")

    print("")
    print(f"Resolved audit JSON: {audit_json}")
    print(f"Resolved audit Markdown: {audit_md}")
    exit_code = run_command(command, dry_run=args.dry_run, allow_failure=args.allow_findings)
    if args.allow_findings and exit_code:
        print("Strict audit found issues; draft mode continued because --allow-findings was set.")


def write_run_summary(
    items: List[PipelineItem],
    item_paths: List[Dict[str, Path]],
    args: argparse.Namespace,
) -> None:
    if not args.run_summary_json:
        return
    summary_path = resolve_path(args.run_summary_json)
    payload = {
        "schema_version": "pdf_structure_pipeline_run.v1",
        "created_at": now_iso(),
        "extraction_engine": args.extraction_engine,
        "allow_findings": bool(args.allow_findings),
        "documents": [],
    }
    for item, paths in zip(items, item_paths):
        payload["documents"].append(
            {
                "document_id": item.document_id,
                "version_label": item.version_label,
                "rule_type": item.rule_type,
                "pdf_path": str(item.pdf_path),
                "paths": {key: str(value) for key, value in paths.items()},
            }
        )
    if args.dry_run:
        print(f"Run summary would be written: {summary_path}")
        return
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Run summary written: {summary_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run shared PDF structure pipeline with Evidence and strict audit gate.")
    parser.add_argument("--manifest", help="JSON list of documents to process.")
    parser.add_argument("--pdf", help="Single PDF path.")
    parser.add_argument("--document-id", help="Single PDF document id.")
    parser.add_argument("--version-label", help="Single PDF version label.")
    parser.add_argument("--rule-type", help="Single PDF rule type.")
    parser.add_argument("--raw-text-dir", default="tmp/pdfs")
    parser.add_argument("--json-dir", default="2_结构化产物/json")
    parser.add_argument("--markdown-dir", default="2_结构化产物/markdown")
    parser.add_argument("--evidence-dir", default="2_结构化产物/evidence")
    parser.add_argument("--audit-output-json")
    parser.add_argument("--audit-output-md")
    parser.add_argument(
        "--extraction-engine",
        choices=("pypdf", "mineru"),
        default="pypdf",
        help="Use pypdf native extraction or local MinerU as the first parser.",
    )
    parser.add_argument("--mineru-output-root", default="tmp/pdfs/mineru_local")
    parser.add_argument(
        "--mineru-safe-input-dir",
        default="tmp/pdfs/mineru_inputs",
        help="Directory for ASCII runtime PDF copies used by local MinerU.",
    )
    parser.add_argument("--mineru-command", default="mineru")
    parser.add_argument("--mineru-api-url")
    parser.add_argument("--mineru-backend", default="pipeline")
    parser.add_argument("--mineru-method", default="auto")
    parser.add_argument("--mineru-lang", default="ch")
    parser.add_argument("--mineru-model-source", default="modelscope")
    parser.add_argument("--mineru-start-page", type=int, help="MinerU zero-based start page.")
    parser.add_argument("--mineru-end-page", type=int, help="MinerU zero-based end page.")
    parser.add_argument("--disable-mineru-formula", action="store_true")
    parser.add_argument("--disable-mineru-table", action="store_true")
    parser.add_argument("--no-mineru-safe-copy", action="store_true")
    parser.add_argument("--reuse-mineru-output", action="store_true")
    parser.add_argument("--run-summary-json")
    parser.add_argument("--include-review-notes", action="store_true")
    parser.add_argument("--enable-formula-markdown", action="store_true")
    parser.add_argument("--enable-appendix-markdown", action="store_true")
    parser.add_argument("--allow-findings", action="store_true", help="Continue in draft mode even when strict audit finds issues.")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    items = build_items(args)
    item_paths = [run_item(item, args) for item in items]
    run_audit(item_paths, args)
    write_run_summary(items, item_paths, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
