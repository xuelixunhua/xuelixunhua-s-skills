# Workflow Patterns

## Start With Strategy, Not Steps

Before writing a workflow, define the reasoning pattern that should guide it:

1. What counts as success?
2. What is the best starting point?
3. What evidence should cause a course correction?
4. What is the stop condition?

This keeps the skill from becoming a brittle checklist. Add explicit steps only when the work is fragile, order-dependent, or safety-critical.

## Philosophy-First Pattern

Use this when the task varies a lot but still needs a stable way of thinking:

```markdown
## Strategy philosophy

1. Define the success criteria.
2. Choose the most informative first move.
3. Treat every intermediate result as evidence.
4. Stop when the success criteria are met.
```

This pattern works well for research, debugging, triage, and other tasks where rigid procedures would over-constrain the model.

## Sequential Workflows

Use explicit sequences when the job really does have a narrow safe path:

```markdown
Filling this form works best in this order:

1. Inspect the form fields.
2. Build the mapping file.
3. Validate the mapping.
4. Fill the form.
5. Verify the output visually.
```

If you reach for a numbered list, ask whether each step is genuinely necessary or whether it should be replaced by a decision point or heuristic.

## Decision Workflows

Use branching logic when different cases require different tactics:

```markdown
1. Determine the modification type.
   - Creating new content: follow the creation branch
   - Editing existing content: follow the editing branch

2. Creation branch: [steps or heuristics]
3. Editing branch: [steps or heuristics]
```

Decision workflows are often better than one long master checklist because they preserve flexibility without becoming vague.

## Subagent Prompting Pattern

When a main agent delegates work, write the subagent prompt around the goal, deliverables, and constraints. Avoid path-locking verbs unless the path is part of the requirement.

Better:

```text
Find the best current explanation of why build times regressed this week.
Return the likely causes, the evidence, and the strongest next check.
```

Worse:

```text
Search for build regressions and grep these two files first.
```

Word choice becomes an implicit rule. A prompt that says "search" may block the subagent from considering better approaches such as reading logs, checking history, or comparing artifacts.
