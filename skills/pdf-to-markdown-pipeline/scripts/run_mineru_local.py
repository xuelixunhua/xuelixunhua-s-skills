#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run local MinerU and record the output directory for the shared PDF pipeline.

This script is a thin boundary around the MinerU CLI. It does not interpret
MinerU results; use mineru_adapter.py for conversion into this workspace's
raw-text/report/evidence seed inputs.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LOCALHOST_NO_PROXY = ["127.0.0.1", "localhost"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def resolve_input_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    if not path.exists():
        raise SystemExit(f"Input PDF does not exist: {path}")
    return path


def resolve_output_path(raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    path = Path(raw_path).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def parse_bool(raw_value: str) -> bool:
    value = str(raw_value).strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {raw_value}")


def merge_no_proxy(existing: str | None) -> str:
    values = []
    if existing:
        values.extend(item.strip() for item in existing.split(",") if item.strip())
    for item in LOCALHOST_NO_PROXY:
        if item not in values:
            values.append(item)
    return ",".join(values)


def build_environment(args: argparse.Namespace) -> dict[str, str]:
    env = os.environ.copy()
    if args.model_source:
        env["MINERU_MODEL_SOURCE"] = args.model_source
    env["NO_PROXY"] = merge_no_proxy(env.get("NO_PROXY"))
    env["no_proxy"] = merge_no_proxy(env.get("no_proxy"))
    return env


def build_command(args: argparse.Namespace, input_pdf: Path, output_root: Path) -> list[str]:
    command = [
        args.mineru_command,
        "-p",
        str(input_pdf),
        "-o",
        str(output_root),
        "-b",
        args.backend,
        "-m",
        args.method,
        "-l",
        args.lang,
        "-f",
        bool_text(args.formula),
        "-t",
        bool_text(args.table),
    ]
    if args.api_url:
        command.extend(["--api-url", args.api_url])
    if args.start_page is not None:
        command.extend(["-s", str(args.start_page)])
    if args.end_page is not None:
        command.extend(["-e", str(args.end_page)])
    return command


def find_auto_dirs(output_root: Path) -> list[Path]:
    if not output_root.exists():
        return []
    matches = []
    for directory in output_root.rglob("*"):
        if not directory.is_dir():
            continue
        if directory.name not in {"auto", "ocr"}:
            continue
        if list(directory.glob("*_content_list.json")):
            matches.append(directory.resolve())
    return sorted(matches, key=lambda path: str(path))


def choose_auto_dir(output_root: Path, input_pdf: Path) -> Path | None:
    matches = find_auto_dirs(output_root)
    if not matches:
        return None
    stem = input_pdf.stem
    preferred = [path for path in matches if stem in str(path)]
    if preferred:
        return preferred[0]
    return matches[0]


def command_exists(command: str) -> bool:
    if Path(command).exists():
        return True
    return shutil.which(command) is not None


def write_manifest(
    manifest_path: Path,
    args: argparse.Namespace,
    input_pdf: Path,
    output_root: Path,
    command: list[str],
    auto_dir: Path | None,
    return_code: int,
) -> None:
    payload: dict[str, Any] = {
        "schema_version": "mineru_local_run.v1",
        "created_at": now_iso(),
        "input_pdf": str(input_pdf),
        "output_root": str(output_root),
        "auto_dir": str(auto_dir) if auto_dir else None,
        "command": command,
        "return_code": return_code,
        "backend": args.backend,
        "method": args.method,
        "lang": args.lang,
        "formula": args.formula,
        "table": args.table,
        "api_url": args.api_url,
        "start_page_zero_based": args.start_page,
        "end_page_zero_based": args.end_page,
        "first_physical_page_number": (args.start_page + 1) if args.start_page is not None else 1,
        "model_source": args.model_source,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local MinerU for one PDF")
    parser.add_argument("--input-pdf", required=True)
    parser.add_argument("--output-root", default="tmp/pdfs/mineru_local")
    parser.add_argument("--manifest-json", help="Optional JSON manifest for downstream adapter use.")
    parser.add_argument("--mineru-command", default=os.environ.get("MINERU_COMMAND", "mineru"))
    parser.add_argument("--api-url", help="Optional local MinerU FastAPI URL.")
    parser.add_argument("--backend", default="pipeline")
    parser.add_argument("--method", default="auto")
    parser.add_argument("--lang", default="ch")
    parser.add_argument("--model-source", default=os.environ.get("MINERU_MODEL_SOURCE", "modelscope"))
    parser.add_argument("--start-page", type=int, help="MinerU zero-based start page.")
    parser.add_argument("--end-page", type=int, help="MinerU zero-based end page.")
    parser.add_argument("--formula", type=parse_bool, default=True)
    parser.add_argument("--table", type=parse_bool, default=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    input_pdf = resolve_input_path(args.input_pdf)
    output_root = resolve_output_path(args.output_root)
    if output_root is None:
        raise SystemExit("--output-root is required")
    output_root.mkdir(parents=True, exist_ok=True)

    manifest_path = resolve_output_path(args.manifest_json) if args.manifest_json else None
    command = build_command(args, input_pdf, output_root)

    print(f"Resolved input PDF: {input_pdf}")
    print(f"Resolved MinerU output root: {output_root}")
    if manifest_path:
        print(f"Resolved MinerU manifest: {manifest_path}")
    print("Command:", subprocess.list2cmdline(command))

    if not command_exists(args.mineru_command):
        raise SystemExit(
            f"MinerU command not found: {args.mineru_command}. "
            "Pass --mineru-command or set MINERU_COMMAND."
        )

    if args.dry_run:
        if manifest_path:
            write_manifest(manifest_path, args, input_pdf, output_root, command, None, 0)
        return 0

    result = subprocess.run(command, cwd=str(Path.cwd()), env=build_environment(args))
    auto_dir = choose_auto_dir(output_root, input_pdf)
    if manifest_path:
        write_manifest(manifest_path, args, input_pdf, output_root, command, auto_dir, result.returncode)

    if result.returncode:
        return result.returncode
    if auto_dir is None:
        raise SystemExit(f"MinerU finished but no auto output was found under: {output_root}")
    print(f"Resolved MinerU auto dir: {auto_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
