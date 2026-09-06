#!/usr/bin/env python3
"""Run isolated implicit-trigger evals for content-master with Codex CLI."""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
TARGET_SKILL = SKILL_ROOT.name
TARGET_SKILL_FILE = SKILL_ROOT / "SKILL.md"
DEFAULT_CASES = SKILL_ROOT / "evals" / "trigger-evals.json"
DEFAULT_RESULTS_DIR = SKILL_ROOT / "evals" / "results"
RUNNER_VERSION = 1

SKILL_PATH_RE = re.compile(r"(?i)/skills/(?:\.system/)?([^/\"']+)/skill\.md")
READ_HINTS = ("get-content", "cat ", "type ", "read_file", "read_text_file")


@dataclass(frozen=True)
class RunConfig:
    codex: str
    model: str | None
    timeout_seconds: float
    other_skill_grace_seconds: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run each raw prompt in a fresh ephemeral Codex session and detect "
            "whether content-master/SKILL.md was actually read."
        )
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--case-id", action="append", default=[])
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--timeout-seconds", type=float, default=40.0)
    parser.add_argument("--other-skill-grace-seconds", type=float, default=3.0)
    parser.add_argument("--model")
    parser.add_argument("--validate-only", action="store_true")
    return parser.parse_args()


def load_suite(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or not isinstance(data.get("cases"), list):
        raise ValueError("trigger eval file must contain a top-level 'cases' array")
    if data.get("skill_name") != TARGET_SKILL:
        raise ValueError(
            f"suite targets {data.get('skill_name')!r}, expected {TARGET_SKILL!r}"
        )

    seen_ids: set[str] = set()
    for index, case in enumerate(data["cases"], start=1):
        if not isinstance(case, dict):
            raise ValueError(f"case #{index} must be an object")
        case_id = case.get("id")
        prompt = case.get("prompt")
        label = case.get("should_trigger")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"case #{index} has an invalid id")
        if case_id in seen_ids:
            raise ValueError(f"duplicate case id: {case_id}")
        seen_ids.add(case_id)
        if not isinstance(prompt, str) or not prompt.strip():
            raise ValueError(f"case {case_id} has an empty prompt")
        if not isinstance(label, bool):
            raise ValueError(f"case {case_id} should_trigger must be boolean")
        lowered = prompt.casefold()
        if TARGET_SKILL.casefold() in lowered or f"${TARGET_SKILL}" in lowered:
            raise ValueError(f"case {case_id} leaks the target skill name")
    return data


def resolve_codex() -> str:
    if os.name == "nt":
        npm_launcher = shutil.which("codex.cmd")
        if npm_launcher:
            npm_root = Path(npm_launcher).resolve().parent
            matches = sorted(
                (npm_root / "node_modules" / "@openai" / "codex").glob(
                    "node_modules/@openai/codex-win32-*/vendor/*/bin/codex.exe"
                )
            )
            if matches:
                return str(matches[0])
            return npm_launcher
    executable = shutil.which("codex")
    if not executable:
        raise FileNotFoundError("codex executable was not found on PATH")
    return executable


def codex_version(codex: str) -> str:
    completed = subprocess.run(
        [codex, "--version"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"codex --version failed: {completed.stdout.strip()}")
    return completed.stdout.strip()


def normalize_command(command: str) -> str:
    return command.replace("\\\\", "/").replace("\\", "/").casefold()


def is_skill_read_command(command: str) -> bool:
    lowered = command.casefold()
    return any(hint in lowered for hint in READ_HINTS)


def target_skill_read_completed(event: dict[str, Any]) -> bool:
    if event.get("type") != "item.completed":
        return False
    item = event.get("item") or {}
    if item.get("type") != "command_execution" or item.get("exit_code") != 0:
        return False
    command = str(item.get("command") or "")
    if not is_skill_read_command(command):
        return False
    target = normalize_command(str(TARGET_SKILL_FILE))
    return target in normalize_command(command)


def skills_in_command(event: dict[str, Any]) -> list[str]:
    if event.get("type") not in {"item.started", "item.completed"}:
        return []
    item = event.get("item") or {}
    if item.get("type") != "command_execution":
        return []
    command = str(item.get("command") or "")
    if not is_skill_read_command(command):
        return []
    return list(dict.fromkeys(SKILL_PATH_RE.findall(normalize_command(command))))


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def stream_lines(stream: Any, output: queue.Queue[str | None]) -> None:
    try:
        for line in iter(stream.readline, ""):
            output.put(line)
    finally:
        output.put(None)


def truncate(text: str, limit: int = 500) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def build_command(config: RunConfig, case_dir: Path, prompt: str) -> list[str]:
    command = [
        config.codex,
        "-a",
        "never",
        "-s",
        "read-only",
        "-C",
        str(case_dir),
    ]
    if config.model:
        command.extend(["-m", config.model])
    command.extend(
        [
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--json",
            "--color",
            "never",
            prompt,
        ]
    )
    return command


def run_case(
    case: dict[str, Any], index: int, work_root: Path, config: RunConfig
) -> dict[str, Any]:
    case_dir = work_root / f"{index:03d}-{case['id']}"
    case_dir.mkdir(parents=True, exist_ok=True)
    command = build_command(config, case_dir, case["prompt"])
    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    env["NO_COLOR"] = "1"

    started = time.monotonic()
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        env=env,
    )
    assert process.stdout is not None
    lines: queue.Queue[str | None] = queue.Queue()
    reader = threading.Thread(target=stream_lines, args=(process.stdout, lines), daemon=True)
    reader.start()

    target_triggered = False
    target_evidence = ""
    selected_skills: list[str] = []
    non_json_lines: list[str] = []
    first_agent_message = ""
    thread_id = ""
    turn_completed = False
    reader_finished = False
    other_skill_seen_at: float | None = None
    stop_reason = "process_exited"
    terminated_by_runner = False

    while True:
        elapsed = time.monotonic() - started
        if elapsed >= config.timeout_seconds:
            stop_reason = "timeout"
            terminated_by_runner = True
            terminate_process_tree(process)
            break
        if (
            other_skill_seen_at is not None
            and elapsed - other_skill_seen_at >= config.other_skill_grace_seconds
        ):
            stop_reason = "other_skill_decision_observed"
            terminated_by_runner = True
            terminate_process_tree(process)
            break

        try:
            raw_line = lines.get(timeout=0.1)
        except queue.Empty:
            if process.poll() is not None and reader_finished:
                break
            continue

        if raw_line is None:
            reader_finished = True
            if process.poll() is not None:
                break
            continue

        stripped = raw_line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            if len(non_json_lines) < 10:
                non_json_lines.append(truncate(stripped))
            continue

        if event.get("type") == "thread.started":
            thread_id = str(event.get("thread_id") or "")
        if event.get("type") == "item.completed":
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and not first_agent_message:
                first_agent_message = truncate(str(item.get("text") or ""))

        observed = skills_in_command(event)
        for skill in observed:
            if skill not in selected_skills:
                selected_skills.append(skill)
        if observed and TARGET_SKILL not in observed and other_skill_seen_at is None:
            other_skill_seen_at = elapsed

        if target_skill_read_completed(event):
            target_triggered = True
            if TARGET_SKILL not in selected_skills:
                selected_skills.append(TARGET_SKILL)
            item = event.get("item") or {}
            target_evidence = truncate(str(item.get("command") or ""), limit=800)
            stop_reason = "target_skill_read_completed"
            terminated_by_runner = True
            terminate_process_tree(process)
            break

        if event.get("type") == "turn.completed":
            turn_completed = True
            stop_reason = "turn_completed"
            break

    if process.poll() is None and not turn_completed:
        terminated_by_runner = True
        terminate_process_tree(process)
    try:
        exit_code = process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        terminate_process_tree(process)
        exit_code = process.returncode
    reader.join(timeout=2)
    duration = round(time.monotonic() - started, 3)

    if target_triggered:
        valid = True
    elif stop_reason == "other_skill_decision_observed":
        valid = True
    elif turn_completed or (exit_code == 0 and stop_reason == "process_exited"):
        valid = True
    else:
        valid = False

    expected = bool(case["should_trigger"])
    if not valid:
        outcome = "INVALID"
        passed: bool | None = None
    elif expected and target_triggered:
        outcome = "TP"
        passed = True
    elif expected and not target_triggered:
        outcome = "FN"
        passed = False
    elif not expected and target_triggered:
        outcome = "FP"
        passed = False
    else:
        outcome = "TN"
        passed = True

    return {
        "index": index,
        "id": case["id"],
        "category": case.get("category", ""),
        "prompt": case["prompt"],
        "rationale": case.get("rationale", ""),
        "should_trigger": expected,
        "observed_trigger": target_triggered,
        "valid": valid,
        "passed": passed,
        "outcome": outcome,
        "selected_skills": selected_skills,
        "stop_reason": stop_reason,
        "duration_seconds": duration,
        "exit_code": exit_code,
        "terminated_by_runner": terminated_by_runner,
        "thread_id": thread_id,
        "target_evidence": target_evidence,
        "first_agent_message": first_agent_message,
        "diagnostics": non_json_lines,
    }


def safe_ratio(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def calculate_metrics(results: Iterable[dict[str, Any]]) -> dict[str, Any]:
    result_list = list(results)
    counts = {label: sum(r["outcome"] == label for r in result_list) for label in ("TP", "FN", "FP", "TN", "INVALID")}
    tp, fn, fp, tn = counts["TP"], counts["FN"], counts["FP"], counts["TN"]
    valid = tp + fn + fp + tn
    precision = safe_ratio(tp, tp + fp)
    recall = safe_ratio(tp, tp + fn)
    specificity = safe_ratio(tn, tn + fp)
    f1 = None
    if precision is not None and recall is not None and precision + recall > 0:
        f1 = round(2 * precision * recall / (precision + recall), 4)
    return {
        **counts,
        "total_cases": len(result_list),
        "valid_cases": valid,
        "passed_cases": tp + tn,
        "accuracy": safe_ratio(tp + tn, valid),
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "f1": f1,
    }


def format_metric(value: Any) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.1%}"
    return str(value)


def markdown_report(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    lines = [
        "# content-master Trigger Eval",
        "",
        f"- Run: `{report['run_id']}`",
        f"- Codex: `{report['codex_version']}`",
        f"- Model: `{report['model']}`",
        f"- Cases: {metrics['valid_cases']}/{metrics['total_cases']} valid",
        f"- Accuracy: {format_metric(metrics['accuracy'])}",
        f"- Precision: {format_metric(metrics['precision'])}",
        f"- Recall: {format_metric(metrics['recall'])}",
        f"- Specificity: {format_metric(metrics['specificity'])}",
        f"- F1: {format_metric(metrics['f1'])}",
        "",
        "## Confusion matrix",
        "",
        "| Expected / observed | Triggered | Not triggered |",
        "| --- | ---: | ---: |",
        f"| Should trigger | {metrics['TP']} TP | {metrics['FN']} FN |",
        f"| Should not trigger | {metrics['FP']} FP | {metrics['TN']} TN |",
        "",
        "## Cases",
        "",
        "| ID | Expected | Observed | Result | Other/loaded skills | Seconds |",
        "| --- | --- | --- | --- | --- | ---: |",
    ]
    for result in report["results"]:
        loaded = ", ".join(result["selected_skills"]) or "—"
        lines.append(
            "| {id} | {expected} | {observed} | {outcome} | {loaded} | {seconds:.3f} |".format(
                id=result["id"],
                expected="yes" if result["should_trigger"] else "no",
                observed="yes" if result["observed_trigger"] else "no",
                outcome=result["outcome"],
                loaded=loaded.replace("|", "\\|"),
                seconds=result["duration_seconds"],
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation boundary",
            "",
            "This suite measures whether the target `SKILL.md` is actually read in a fresh ephemeral session. "
            "It does not grade the quality of the final answer. Positive detections terminate immediately "
            "after the target Skill read completes; specialist negatives terminate after the configured "
            "decision grace window to avoid executing the full task.",
            "",
        ]
    )
    return "\n".join(lines)


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def main() -> int:
    args = parse_args()
    suite_path = args.cases.resolve()
    suite = load_suite(suite_path)
    selected_cases = suite["cases"]
    if args.case_id:
        requested = set(args.case_id)
        selected_cases = [case for case in selected_cases if case["id"] in requested]
        missing = requested - {case["id"] for case in selected_cases}
        if missing:
            raise ValueError(f"unknown case id(s): {', '.join(sorted(missing))}")
    if not selected_cases:
        raise ValueError("no trigger eval cases selected")
    if args.jobs < 1:
        raise ValueError("--jobs must be at least 1")
    if args.timeout_seconds <= 0 or args.other_skill_grace_seconds <= 0:
        raise ValueError("timeout and grace values must be positive")

    codex = resolve_codex()
    version = codex_version(codex)
    if args.validate_only:
        print(f"Valid: {len(selected_cases)} cases; {version}; target={TARGET_SKILL_FILE}")
        return 0

    config = RunConfig(
        codex=codex,
        model=args.model,
        timeout_seconds=args.timeout_seconds,
        other_skill_grace_seconds=args.other_skill_grace_seconds,
    )
    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%dT%H%M%SZ")
    results: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="content-master-trigger-eval-") as temp_dir:
        work_root = Path(temp_dir)
        with ThreadPoolExecutor(max_workers=min(args.jobs, len(selected_cases))) as executor:
            future_map = {
                executor.submit(run_case, case, index, work_root, config): case["id"]
                for index, case in enumerate(selected_cases, start=1)
            }
            for future in as_completed(future_map):
                result = future.result()
                results.append(result)
                print(
                    f"[{len(results):02d}/{len(selected_cases):02d}] "
                    f"{result['id']}: {result['outcome']} "
                    f"({result['duration_seconds']:.3f}s)"
                )

    results.sort(key=lambda item: item["index"])
    metrics = calculate_metrics(results)
    finished_at = datetime.now(timezone.utc)
    report = {
        "report_version": 1,
        "runner_version": RUNNER_VERSION,
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": round((finished_at - started_at).total_seconds(), 3),
        "suite_path": str(suite_path),
        "suite_version": suite.get("suite_version"),
        "target_skill": TARGET_SKILL,
        "target_skill_file": str(TARGET_SKILL_FILE),
        "codex_executable": codex,
        "codex_version": version,
        "model": args.model or "config default",
        "jobs": args.jobs,
        "timeout_seconds": args.timeout_seconds,
        "other_skill_grace_seconds": args.other_skill_grace_seconds,
        "metrics": metrics,
        "results": results,
    }

    results_dir = args.results_dir.resolve()
    json_path = results_dir / "trigger-eval-latest.json"
    markdown_path = results_dir / "trigger-eval-latest.md"
    atomic_write(json_path, json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    atomic_write(markdown_path, markdown_report(report))
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {markdown_path}")
    print(
        "Summary: "
        f"accuracy={format_metric(metrics['accuracy'])}, "
        f"precision={format_metric(metrics['precision'])}, "
        f"recall={format_metric(metrics['recall'])}, "
        f"invalid={metrics['INVALID']}"
    )
    return 0 if metrics["INVALID"] == 0 else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (FileNotFoundError, RuntimeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
