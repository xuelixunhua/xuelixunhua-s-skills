#!/usr/bin/env python3
"""
OpenAI YAML Generator - Creates or updates agents/openai.yaml in UTF-8.

Included from the OpenAI-bundled Skill Creator under Apache-2.0 so the
user-maintained Skill Creator can perform the full creation workflow itself.

Usage:
    generate_openai_yaml.py <skill_dir> [--name <skill_name>] [--interface key=value]
"""

import argparse
import re
import sys
import tempfile
from pathlib import Path

import yaml

ACRONYMS = {
    "GH",
    "MCP",
    "API",
    "CI",
    "CLI",
    "LLM",
    "PDF",
    "PR",
    "UI",
    "URL",
    "SQL",
}

BRANDS = {
    "openai": "OpenAI",
    "openapi": "OpenAPI",
    "github": "GitHub",
    "pagerduty": "PagerDuty",
    "datadog": "DataDog",
    "sqlite": "SQLite",
    "fastapi": "FastAPI",
}

SMALL_WORDS = {"and", "or", "to", "up", "with"}

ALLOWED_INTERFACE_KEYS = {
    "display_name",
    "short_description",
    "icon_small",
    "icon_large",
    "brand_color",
    "default_prompt",
}


def format_display_name(skill_name):
    words = [word for word in skill_name.split("-") if word]
    formatted = []
    for index, word in enumerate(words):
        lower = word.lower()
        upper = word.upper()
        if upper in ACRONYMS:
            formatted.append(upper)
            continue
        if lower in BRANDS:
            formatted.append(BRANDS[lower])
            continue
        if index > 0 and lower in SMALL_WORDS:
            formatted.append(lower)
            continue
        formatted.append(word.capitalize())
    return " ".join(formatted)


def generate_short_description(display_name):
    description = f"Help with {display_name} tasks"

    if len(description) < 25:
        description = f"Help with {display_name} tasks and workflows"
    if len(description) < 25:
        description = f"Help with {display_name} tasks with guidance"

    if len(description) > 64:
        description = f"Help with {display_name}"
    if len(description) > 64:
        description = f"{display_name} helper"
    if len(description) > 64:
        description = f"{display_name} tools"
    if len(description) > 64:
        suffix = " helper"
        max_name_length = 64 - len(suffix)
        trimmed = display_name[:max_name_length].rstrip()
        description = f"{trimmed}{suffix}"
    if len(description) > 64:
        description = description[:64].rstrip()

    if len(description) < 25:
        description = f"{description} workflows"
        if len(description) > 64:
            description = description[:64].rstrip()

    return description


def read_frontmatter_name(skill_dir):
    skill_md = Path(skill_dir) / "SKILL.md"
    if not skill_md.exists():
        print(f"[ERROR] SKILL.md not found in {skill_dir}")
        return None
    try:
        content = skill_md.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        print(f"[ERROR] Cannot read SKILL.md as UTF-8: {exc}")
        return None
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not match:
        print("[ERROR] Invalid SKILL.md frontmatter format.")
        return None
    frontmatter_text = match.group(1)

    try:
        frontmatter = yaml.safe_load(frontmatter_text)
    except yaml.YAMLError as exc:
        print(f"[ERROR] Invalid YAML frontmatter: {exc}")
        return None
    if not isinstance(frontmatter, dict):
        print("[ERROR] Frontmatter must be a YAML dictionary.")
        return None
    name = frontmatter.get("name", "")
    if not isinstance(name, str) or not name.strip():
        print("[ERROR] Frontmatter 'name' is missing or invalid.")
        return None
    return name.strip()


def parse_interface_overrides(raw_overrides):
    overrides = {}
    for item in raw_overrides:
        if "=" not in item:
            print(f"[ERROR] Invalid interface override '{item}'. Use key=value.")
            return None
        key, value = item.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            print(f"[ERROR] Invalid interface override '{item}'. Key is empty.")
            return None
        if key not in ALLOWED_INTERFACE_KEYS:
            allowed = ", ".join(sorted(ALLOWED_INTERFACE_KEYS))
            print(f"[ERROR] Unknown interface field '{key}'. Allowed: {allowed}")
            return None
        overrides[key] = value
    return overrides


def write_openai_yaml(skill_dir, skill_name, raw_overrides):
    """Merge explicit interface changes while preserving other configuration values."""
    overrides = parse_interface_overrides(raw_overrides)
    if overrides is None:
        return None

    agents_dir = Path(skill_dir) / "agents"
    output_path = agents_dir / "openai.yaml"
    data = {}
    if output_path.exists():
        try:
            data = yaml.safe_load(output_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
            print(f"[ERROR] Cannot read existing openai.yaml; left unchanged: {exc}")
            return None
        if not isinstance(data, dict):
            print("[ERROR] Existing openai.yaml must be a mapping; left unchanged.")
            return None

    interface = data.get("interface", {})
    if not isinstance(interface, dict):
        print("[ERROR] Existing interface must be a mapping; left unchanged.")
        return None
    interface = {**interface, **overrides}
    interface.setdefault("display_name", format_display_name(skill_name))
    if not isinstance(interface["display_name"], str) or not interface["display_name"].strip():
        print("[ERROR] display_name must be a non-empty string.")
        return None
    interface.setdefault(
        "short_description", generate_short_description(interface["display_name"])
    )
    for key in ALLOWED_INTERFACE_KEYS & interface.keys():
        if not isinstance(interface[key], str) or not interface[key].strip():
            print(f"[ERROR] interface.{key} must be a non-empty string.")
            return None
    if not (25 <= len(interface["short_description"]) <= 64):
        print("[WARN] Prefer a 25-64 character short_description for UI readability.")
    data["interface"] = interface

    temporary_path = None
    try:
        # Serialize before opening any output; malformed values cannot truncate it.
        content = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
        agents_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="\n", dir=agents_dir,
            prefix=".openai-", suffix=".tmp", delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
        temporary_path.replace(output_path)
    except (OSError, yaml.YAMLError) as exc:
        print(f"[ERROR] Could not write openai.yaml: {exc}")
        return None
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()
    print("[OK] Wrote agents/openai.yaml (unmodified configuration values preserved)")
    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Create or update agents/openai.yaml, preserving existing configuration values.",
    )
    parser.add_argument("skill_dir", help="Path to the skill directory")
    parser.add_argument(
        "--name",
        help="Skill name override (defaults to SKILL.md frontmatter)",
    )
    parser.add_argument(
        "--interface",
        action="append",
        default=[],
        help="Interface override in key=value format (repeatable)",
    )
    args = parser.parse_args()

    skill_dir = Path(args.skill_dir).resolve()
    if not skill_dir.exists():
        print(f"[ERROR] Skill directory not found: {skill_dir}")
        sys.exit(1)
    if not skill_dir.is_dir():
        print(f"[ERROR] Path is not a directory: {skill_dir}")
        sys.exit(1)

    skill_name = args.name or read_frontmatter_name(skill_dir)
    if not skill_name:
        sys.exit(1)

    result = write_openai_yaml(skill_dir, skill_name, args.interface)
    if result:
        sys.exit(0)
    sys.exit(1)


if __name__ == "__main__":
    main()
