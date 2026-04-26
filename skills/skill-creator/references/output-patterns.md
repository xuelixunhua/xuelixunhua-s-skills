# Output Patterns

Use these patterns when presenting prompt or skill design work to the user.

## Match Strictness To Fragility

Be strict only when a downstream consumer or risky workflow needs it.

- Strict structure is good for machine-readable outputs, validation targets, or fragile workflows.
- Flexible structure is better when the model needs room to adapt to the situation.

If you find yourself reaching for "ALWAYS" or "NEVER", check whether you are protecting something real or merely removing judgment.

## Prompt Repair Output

When revising a prompt, this structure is often useful:

```text
## Goal
[What the prompt is trying to accomplish]

## Diagnosis
- [What is weak in the current draft]
- [What should be preserved]

## Revised Prompt
[Place the revised prompt here, usually in a fenced code block]

## Why This Version Is Better
- [Reason 1]
- [Reason 2]

## Test Inputs
- [Realistic user request]
- [Realistic edge case]
```

## Skill Design Output

When revising or designing a skill, this structure is often useful:

```text
## Packaging Decision
[Why this should be a skill rather than a prompt or global rule]

## Boundary
- Triggers:
- Near misses:

## Strategy Philosophy
[Reasoning pattern]

## Resource Plan
- scripts/:
- references/:
- assets/:

## Eval Plan
- [Realistic prompt 1]
- [Realistic prompt 2]
```

## Strict Template Pattern

Use this when the output must follow a stable machine-checked layout:

```text
## Report structure

Use this exact template:

# [Title]
## Executive summary
## Key findings
## Recommendations
```

## Flexible Default Pattern

Use this when structure is helpful but adaptation matters:

```text
## Report structure

Use this as the default shape unless the task suggests a better fit:

# [Title]
## Executive summary
## Findings
## Recommendations
```

## Example Pattern

Examples are useful when style matters more than rules:

```text
## Commit message examples

Example input: Added user authentication with JWT tokens
Example output: feat(auth): implement JWT-based authentication
```
