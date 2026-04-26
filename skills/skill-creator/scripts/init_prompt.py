#!/usr/bin/env python3
"""
Prompt initializer that creates a reusable prompt scaffold.

Usage:
    init_prompt.py <prompt-name> --path <path>

Examples:
    init_prompt.py article-rewriter --path prompts
    init_prompt.py research-summarizer --path C:/Users/me/prompt-library
"""

import sys
from pathlib import Path


PROMPT_TEMPLATE = """# {prompt_title}

## Mission

[TODO: Describe the reusable job this prompt is meant to do.]

## Use When

[TODO: Describe the requests or scenarios where this prompt is the right tool.]

## Role And Audience

- Model role: [TODO]
- Service target or audience: [TODO]

## Inputs To Provide

- [TODO: Situation or source material]
- [TODO: Current state]
- [TODO: Goal]
- [TODO: Constraints]

## Success Criteria

- [TODO: What a good output must achieve]
- [TODO: What failure looks like]

## Prompt

```text
[TODO: Write the actual reusable prompt here.]
```

## Design Notes

- [TODO: What this prompt is optimizing for]
- [TODO: Which phrases or definitions are important]
- [TODO: What you intentionally left flexible]
"""

TEST_INPUTS_TEMPLATE = """# Test Inputs For {prompt_title}

Use these examples to pressure-test the prompt before calling it done.

## Core Cases

1. [TODO: A straightforward realistic request]
2. [TODO: A realistic request with slightly messier context]

## Edge Cases

1. [TODO: A case where the wording is ambiguous]
2. [TODO: A case where the prompt might become too rigid or too vague]

## Review Checklist

- Does the prompt clearly establish role and audience?
- Is the wording concise without dropping key context?
- Are important terms defined precisely enough?
- Does the prompt converge the model toward the intended output?
- Are there any instructions that are decorative rather than functional?
"""


def title_case_name(name):
    """Convert a hyphenated identifier into a display title."""
    return " ".join(word.capitalize() for word in name.split("-"))


def init_prompt(prompt_name, path):
    """Create a reusable prompt scaffold."""
    prompt_dir = Path(path).resolve() / prompt_name

    if prompt_dir.exists():
        print(f"Error: Prompt directory already exists: {prompt_dir}")
        return None

    try:
        prompt_dir.mkdir(parents=True, exist_ok=False)
        print(f"Created prompt directory: {prompt_dir}")
    except Exception as exc:
        print(f"Error creating directory: {exc}")
        return None

    prompt_title = title_case_name(prompt_name)

    try:
        prompt_path = prompt_dir / "PROMPT.md"
        prompt_path.write_text(
            PROMPT_TEMPLATE.format(prompt_title=prompt_title),
            encoding="utf-8",
        )
        print("Created PROMPT.md")

        test_inputs_path = prompt_dir / "TEST_INPUTS.md"
        test_inputs_path.write_text(
            TEST_INPUTS_TEMPLATE.format(prompt_title=prompt_title),
            encoding="utf-8",
        )
        print("Created TEST_INPUTS.md")
    except Exception as exc:
        print(f"Error creating prompt files: {exc}")
        return None

    print(f"\nPrompt '{prompt_name}' initialized successfully at {prompt_dir}")
    print("\nNext steps:")
    print("1. Replace the TODOs in PROMPT.md, starting with Mission, Role And Audience, and Prompt")
    print("2. Add realistic cases in TEST_INPUTS.md before treating the prompt as finished")
    print("3. Run a light evaluation pass with real examples")

    return prompt_dir


def main():
    if len(sys.argv) < 4 or sys.argv[2] != "--path":
        print("Usage: init_prompt.py <prompt-name> --path <path>")
        print("\nPrompt name suggestions:")
        print("  - Prefer lowercase letters, digits, and hyphens")
        print("  - Keep the name short and capability-oriented")
        print("\nExamples:")
        print("  init_prompt.py article-rewriter --path prompts")
        print("  init_prompt.py research-summarizer --path C:/Users/me/prompt-library")
        sys.exit(1)

    prompt_name = sys.argv[1]
    path = sys.argv[3]

    print(f"Initializing prompt: {prompt_name}")
    print(f"Location: {path}\n")

    result = init_prompt(prompt_name, path)
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
