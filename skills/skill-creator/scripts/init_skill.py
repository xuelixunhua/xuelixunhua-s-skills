#!/usr/bin/env python3
"""
Create a concise, philosophy-first skill scaffold.

This combines the user-maintained Skill Creator's design method with selected
current Codex conventions from the OpenAI-bundled Skill Creator.
"""

import argparse
import re
import sys
from pathlib import Path

from generate_openai_yaml import write_openai_yaml


MAX_SKILL_NAME_LENGTH = 64
ALLOWED_RESOURCES = {"scripts", "references", "assets", "evals"}

SKILL_TEMPLATE = """---
name: {skill_name}
description: "TODO: State what capability this skill provides and the requests or contexts that should trigger it."
---

# {skill_title}

## Mission

[TODO: Describe the durable job this skill performs and who it serves.]

## Success Criteria

- [TODO: Define the observable result.]
- [TODO: Define the important quality or safety boundary.]

## Strategy Philosophy

[TODO: Define the direction and tradeoffs that govern this skill: what it prioritizes, how it chooses a route, what evidence changes the approach, and when it is done. Preserve the user's core judgment; avoid generic slogans.]

## Workflow

1. [TODO: Add only the steps whose order or existence materially affects the result.]
2. [TODO]

## Resources

[TODO: Route each required script, reference, asset, or eval. Delete this section if none are needed.]

## Quality Check

- [TODO: Add the smallest checks that catch real failure modes.]
"""

EXAMPLES = {
    "scripts": '''#!/usr/bin/env python3
"""Replace this placeholder with deterministic work that is repeatedly needed."""


def main():
    raise NotImplementedError("Replace or delete this placeholder.")


if __name__ == "__main__":
    main()
''',
    "references": """# Domain Reference

Keep only facts, schemas, examples, or detailed methods that should load on demand.
""",
    "assets": """Replace this placeholder with a template or output asset, or delete it.
""",
    "evals": """# Evaluation Cases

1. Add a representative core request.
2. Add a messy or ambiguous request.
3. Add a near-boundary request that should not over-trigger.
""",
}

EXAMPLE_NAMES = {
    "scripts": "example.py",
    "references": "domain-reference.md",
    "assets": "placeholder.txt",
    "evals": "cases.md",
}


def normalize_skill_name(raw_name):
    """Normalize a proposed name to lowercase hyphen-case."""
    normalized = raw_name.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized


def title_case_skill_name(skill_name):
    """Convert a hyphenated skill name to a readable title."""
    return " ".join(part.capitalize() for part in skill_name.split("-"))


def parse_resources(raw_resources):
    if not raw_resources:
        return []

    resources = [item.strip() for item in raw_resources.split(",") if item.strip()]
    invalid = sorted(set(resources) - ALLOWED_RESOURCES)
    if invalid:
        allowed = ", ".join(sorted(ALLOWED_RESOURCES))
        raise ValueError(
            f"Unknown resource type(s): {', '.join(invalid)}. Allowed: {allowed}"
        )

    return list(dict.fromkeys(resources))


def create_resources(skill_dir, resources, include_examples):
    for resource in resources:
        resource_dir = skill_dir / resource
        resource_dir.mkdir(exist_ok=True)
        print(f"[OK] Created {resource}/")

        if include_examples:
            example_path = resource_dir / EXAMPLE_NAMES[resource]
            example_path.write_text(EXAMPLES[resource], encoding="utf-8")
            print(f"[OK] Created {resource}/{example_path.name}")


def init_skill(skill_name, output_root, resources, include_examples, interfaces):
    skill_dir = Path(output_root).resolve() / skill_name
    if skill_dir.exists():
        print(f"[ERROR] Skill directory already exists: {skill_dir}")
        return None

    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        title = title_case_skill_name(skill_name)
        (skill_dir / "SKILL.md").write_text(
            SKILL_TEMPLATE.format(skill_name=skill_name, skill_title=title),
            encoding="utf-8",
        )
        print(f"[OK] Created {skill_dir / 'SKILL.md'}")

        if not write_openai_yaml(skill_dir, skill_name, interfaces):
            return None

        create_resources(skill_dir, resources, include_examples)
    except Exception as exc:
        print(f"[ERROR] Failed to initialize skill: {exc}")
        return None

    print(f"\n[OK] Initialized '{skill_name}' at {skill_dir}")
    print("Next:")
    print("1. Replace the TODOs with the smallest complete method.")
    print("2. Delete unused sections, folders, and placeholders.")
    print("3. Run scripts/quick_validate.py with --ready from the Skill Creator.")
    print("4. Choose checks proportional to the change; report behavioral evidence separately.")
    return skill_dir


def main():
    parser = argparse.ArgumentParser(
        description="Create a concise, philosophy-first skill scaffold."
    )
    parser.add_argument("skill_name", help="Skill name; normalized to hyphen-case")
    parser.add_argument("--path", required=True, help="Parent directory for the skill")
    parser.add_argument(
        "--resources",
        default="",
        help="Comma-separated list: scripts,references,assets,evals",
    )
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Add minimal placeholders to selected resource folders",
    )
    parser.add_argument(
        "--interface",
        action="append",
        default=[],
        help="agents/openai.yaml override in key=value form; repeat as needed",
    )
    args = parser.parse_args()

    skill_name = normalize_skill_name(args.skill_name)
    if not skill_name:
        print("[ERROR] Skill name must contain at least one letter or digit.")
        sys.exit(1)
    if len(skill_name) > MAX_SKILL_NAME_LENGTH:
        print(
            f"[ERROR] Skill name is {len(skill_name)} characters; "
            f"maximum is {MAX_SKILL_NAME_LENGTH}."
        )
        sys.exit(1)
    if skill_name != args.skill_name:
        print(f"[INFO] Normalized '{args.skill_name}' to '{skill_name}'.")

    try:
        resources = parse_resources(args.resources)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    if args.examples and not resources:
        print("[ERROR] --examples requires at least one --resources value.")
        sys.exit(1)

    result = init_skill(
        skill_name,
        args.path,
        resources,
        args.examples,
        args.interface,
    )
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
