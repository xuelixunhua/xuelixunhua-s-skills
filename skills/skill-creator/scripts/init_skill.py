#!/usr/bin/env python3
"""
Skill initializer that creates a philosophy-first skill scaffold.

Usage:
    init_skill.py <skill-name> --path <path>

Examples:
    init_skill.py my-new-skill --path skills/public
    init_skill.py my-api-helper --path skills/private
    init_skill.py custom-skill --path /custom/location
"""

import sys
from pathlib import Path


SKILL_TEMPLATE = """---
name: {skill_name}
description: [TODO: State what reusable capability this skill provides and when Codex should trigger it. Mention representative requests, adjacent phrasings, and important boundaries.]
---

# {skill_title}

## Mission

[TODO: Describe the durable capability this skill adds. Write the job to be done, not the history of how you discovered it.]

## Success Criteria

[TODO: Define what success looks like.]
- [Example: Produces the right artifact or answer for the user]
- [Example: Uses the preferred tools or resources when they matter]
- [Example: Stops once the success criteria are met]

## Skill Type

[TODO: Choose the dominant shape and delete the others.]
- Fixed workflow for a repeatable job
- Agent framework for a broader capability
- Hybrid of the two when a reusable philosophy wraps a few stable subroutines

## Trigger Surface

[TODO: List the kinds of user requests that should trigger this skill, plus nearby cases that it should absorb instead of splitting into separate skills.]

## Strategy Philosophy

Explain how the agent should think before you explain how it should act.

1. Define the success criteria.
2. Choose the best starting point.
3. Treat intermediate results as evidence and correct course early.
4. Stop when the success criteria are met.

[TODO: Replace this with the domain-specific reasoning pattern for the skill.]

## Minimum Complete Toolkit

[TODO: List the smallest set of tools and resources that make this capability reliable.]
- `scripts/` for repeated deterministic work
- `references/` for detailed facts, schemas, or domain notes
- `assets/` for templates and output materials

## Necessary Facts and Boundaries

[TODO: Record non-obvious facts, preferred entry points, terminology, quality bars, and safety constraints.]
- Known best entry points:
- Important terms:
- Risks or quality boundaries:

## Workflow Or Decision Points

[TODO: Add explicit steps only where the work is fragile, order-dependent, or safety-critical.]
- If ...
- If ...
- Otherwise ...

## Output Guidance

[TODO: Describe the default output shape. Be as strict as the task requires, and no stricter.]

## Examples

[TODO: Add 2-3 realistic user requests that should trigger this skill.]

## Resource Map

[TODO: Explain when to open each reference or run each script.]
"""

EXAMPLE_SCRIPT = '''#!/usr/bin/env python3
"""
Example helper script for {skill_name}

Use scripts for repeated deterministic work that the agent should not keep
reinventing from scratch.
"""


def main():
    print("Replace this placeholder with a real helper for {skill_name}.")


if __name__ == "__main__":
    main()
'''

EXAMPLE_REFERENCE = """# Domain Notes For {skill_title}

Use reference files for facts that are too detailed for SKILL.md but still worth
loading when needed.

## Terminology

- [TODO: Define the important domain terms]

## Preferred Starting Points

- [TODO: Document the best first place to look or the best first command to run]

## Hidden Constraints

- [TODO: Note anything the model may not naturally remember or prioritize]

## Examples

- [TODO: Add a concrete example or edge case when helpful]
"""

EXAMPLE_ASSET = """# Example Asset Placeholder

Use assets for templates, boilerplate projects, images, fonts, or any other file
that should be used in the final output rather than read into context.
"""


def title_case_skill_name(skill_name):
    """Convert a hyphenated skill name to title case."""
    return " ".join(word.capitalize() for word in skill_name.split("-"))


def init_skill(skill_name, path):
    """Initialize a new skill directory with a philosophy-first template."""
    skill_dir = Path(path).resolve() / skill_name

    if skill_dir.exists():
        print(f"Error: Skill directory already exists: {skill_dir}")
        return None

    try:
        skill_dir.mkdir(parents=True, exist_ok=False)
        print(f"Created skill directory: {skill_dir}")
    except Exception as exc:
        print(f"Error creating directory: {exc}")
        return None

    skill_title = title_case_skill_name(skill_name)
    skill_content = SKILL_TEMPLATE.format(
        skill_name=skill_name,
        skill_title=skill_title,
    )

    skill_md_path = skill_dir / "SKILL.md"
    try:
        skill_md_path.write_text(skill_content, encoding="utf-8")
        print("Created SKILL.md")
    except Exception as exc:
        print(f"Error creating SKILL.md: {exc}")
        return None

    try:
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(exist_ok=True)
        example_script = scripts_dir / "example.py"
        example_script.write_text(
            EXAMPLE_SCRIPT.format(skill_name=skill_name),
            encoding="utf-8",
        )
        example_script.chmod(0o755)
        print("Created scripts/example.py")

        references_dir = skill_dir / "references"
        references_dir.mkdir(exist_ok=True)
        example_reference = references_dir / "domain_notes.md"
        example_reference.write_text(
            EXAMPLE_REFERENCE.format(skill_title=skill_title),
            encoding="utf-8",
        )
        print("Created references/domain_notes.md")

        assets_dir = skill_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        example_asset = assets_dir / "example_asset.txt"
        example_asset.write_text(EXAMPLE_ASSET, encoding="utf-8")
        print("Created assets/example_asset.txt")
    except Exception as exc:
        print(f"Error creating resource directories: {exc}")
        return None

    print(f"\nSkill '{skill_name}' initialized successfully at {skill_dir}")
    print("\nNext steps:")
    print("1. Replace the TODOs in SKILL.md, starting with Trigger Surface and Strategy Philosophy")
    print("2. Delete any placeholder resources that do not earn their keep")
    print("3. Run the validator when the skill is ready")

    return skill_dir


def main():
    if len(sys.argv) < 4 or sys.argv[2] != "--path":
        print("Usage: init_skill.py <skill-name> --path <path>")
        print("\nSkill name requirements:")
        print("  - Hyphen-case identifier (e.g. 'data-analyzer')")
        print("  - Lowercase letters, digits, and hyphens only")
        print("  - Max 64 characters")
        print("  - Must match the directory name exactly")
        print("\nExamples:")
        print("  init_skill.py my-new-skill --path skills/public")
        print("  init_skill.py my-api-helper --path skills/private")
        print("  init_skill.py custom-skill --path /custom/location")
        sys.exit(1)

    skill_name = sys.argv[1]
    path = sys.argv[3]

    print(f"Initializing skill: {skill_name}")
    print(f"Location: {path}\n")

    result = init_skill(skill_name, path)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
