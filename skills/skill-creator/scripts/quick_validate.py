#!/usr/bin/env python3
"""
Validate a skill's structure, with optional entry-file readiness checks.

This keeps the OpenAI-bundled validator's useful checks and adds folder-name
and optional agents/openai.yaml validation for the user-maintained creator.
"""

import argparse
import re
import sys
from pathlib import Path

import yaml


MAX_SKILL_NAME_LENGTH = 64
ALLOWED_FRONTMATTER = {
    "name",
    "description",
    "license",
    "allowed-tools",
    "metadata",
}


def read_yaml(path):
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")), None
    except UnicodeDecodeError as exc:
        return None, f"{path.name} must be valid UTF-8: {exc}"
    except yaml.YAMLError as exc:
        return None, f"Invalid YAML in {path.name}: {exc}"
    except OSError as exc:
        return None, f"Cannot read {path.name}: {exc}"


def validate_openai_yaml(path, skill_name, warnings=None):
    warnings = warnings if warnings is not None else []
    data, error = read_yaml(path)
    if error:
        return error
    if not isinstance(data, dict):
        return "agents/openai.yaml must contain a YAML mapping"

    interface = data.get("interface", {})
    if not isinstance(interface, dict):
        return "interface must be a YAML mapping when supplied"

    for key in ("display_name", "short_description", "default_prompt", "icon_small", "icon_large", "brand_color"):
        if key in interface and (
            not isinstance(interface[key], str) or not interface[key].strip()
        ):
            return f"interface.{key} must be a non-empty string when supplied"
    if "short_description" in interface and not (25 <= len(interface["short_description"]) <= 64):
        warnings.append("Prefer a 25-64 character interface.short_description for UI readability.")
    if "default_prompt" in interface and f"${skill_name}" not in interface["default_prompt"]:
        warnings.append(f"Prefer explicitly mentioning ${skill_name} in interface.default_prompt.")

    if "policy" in data:
        policy = data["policy"]
        if not isinstance(policy, dict):
            return "policy must be a YAML mapping when supplied"
        if "allow_implicit_invocation" in policy and not isinstance(policy["allow_implicit_invocation"], bool):
            return "policy.allow_implicit_invocation must be a boolean"

    return None


def check_readiness(skill_path, description, body):
    """Check scaffold markers and literal bundled file paths in SKILL.md only.

    This deliberately does not interpret commands, glob patterns, resource
    contents, or example semantics. Those still need task-specific review.
    """
    issues = []
    if re.match(r"TODO\s*:", description, re.IGNORECASE) or re.search(
        r"\[TODO(?:\]|\s|:)", body, re.IGNORECASE
    ):
        issues.append("Unfinished scaffold markers in SKILL.md")

    candidates = set()
    for code_path, link_path in re.findall(r"`([^`\n]+)`|\[[^\]\n]*\]\(([^)\n]+)\)", body):
        candidate = (code_path or link_path).strip().strip("<>").split("#", 1)[0]
        candidate = candidate.replace("\\", "/").removeprefix("./")
        if not candidate.startswith(("scripts/", "references/", "assets/", "evals/")):
            continue
        if any(char in candidate for char in "*?{}<>$") or not re.search(r"\.[A-Za-z0-9]+$", candidate):
            continue
        candidates.add(candidate)

    for candidate in sorted(candidates):
        target = (skill_path / candidate).resolve()
        if not target.is_relative_to(skill_path):
            issues.append(f"Bundled reference leaves the skill directory: {candidate}")
        elif not target.is_file():
            issues.append(f"Missing bundled file: {candidate}")
    return issues


def validate_skill(skill_path, ready=False):
    skill_path = Path(skill_path).resolve()
    skill_md = skill_path / "SKILL.md"
    warnings = []

    if not skill_md.exists():
        return False, "SKILL.md not found", warnings

    try:
        content = skill_md.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return False, f"SKILL.md must be valid UTF-8: {exc}", warnings
    except OSError as exc:
        return False, f"Cannot read SKILL.md: {exc}", warnings

    match = re.match(r"^---\r?\n(.*?)\r?\n---", content, re.DOTALL)
    if not match:
        return False, "Invalid or missing YAML frontmatter", warnings

    try:
        frontmatter = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        return False, f"Invalid YAML in frontmatter: {exc}", warnings

    if not isinstance(frontmatter, dict):
        return False, "Frontmatter must be a YAML mapping", warnings

    unexpected = set(frontmatter) - ALLOWED_FRONTMATTER
    if unexpected:
        return (
            False,
            f"Unexpected frontmatter key(s): {', '.join(sorted(unexpected))}",
            warnings,
        )

    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not isinstance(name, str) or not name.strip():
        return False, "Frontmatter name must be a non-empty string", warnings
    name = name.strip()

    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        return False, f"Name '{name}' must be lowercase hyphen-case", warnings
    if len(name) > MAX_SKILL_NAME_LENGTH:
        return False, f"Name exceeds {MAX_SKILL_NAME_LENGTH} characters", warnings
    if skill_path.name != name:
        return (
            False,
            f"Folder name '{skill_path.name}' must match frontmatter name '{name}'",
            warnings,
        )

    if not isinstance(description, str) or not description.strip():
        return False, "Frontmatter description must be a non-empty string", warnings
    description = description.strip()
    if len(description) > 1024:
        return False, "Description exceeds 1024 characters", warnings
    if "<" in description or ">" in description:
        return False, "Description cannot contain angle brackets", warnings

    body = content[match.end() :].strip()
    if not body:
        return False, "SKILL.md body is empty", warnings

    line_count = len(content.splitlines())
    if line_count > 500:
        warnings.append(
            f"SKILL.md has {line_count} lines; review whether details should load on demand."
        )

    openai_yaml = skill_path / "agents" / "openai.yaml"
    if openai_yaml.exists():
        interface_error = validate_openai_yaml(openai_yaml, name, warnings)
        if interface_error:
            return False, interface_error, warnings

    if ready:
        issues = check_readiness(skill_path, description, body)
        if issues:
            return False, "Entry-file readiness checks failed:\n- " + "\n- ".join(issues), warnings
    mode = "Structure and entry-file readiness checks" if ready else "Structural checks"
    return True, f"{mode} passed (model behavior not evaluated).", warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("skill_directory")
    parser.add_argument("--ready", action="store_true", help="Also check scaffold markers and literal bundled file references in SKILL.md")
    args = parser.parse_args()

    valid, message, warnings = validate_skill(args.skill_directory, ready=args.ready)
    for warning in warnings:
        print(f"[WARN] {warning}")
    print(message)
    sys.exit(0 if valid else 1)


if __name__ == "__main__":
    main()
