# Prompt Evaluation Guide

## Use The Lightest Eval Loop That Can Catch Real Problems

Prompt evaluation should usually be lighter than skill evaluation. The goal is to see whether the prompt preserves the method, not to build a heavy benchmark by default.

A lightweight loop for behavioral changes is:

1. Draft the prompt
2. Write 2-5 realistic test inputs
3. Run the prompt on those inputs
4. Review the outputs against the success criteria
5. Revise the prompt
6. Repeat only while a failure or meaningful uncertainty remains

For a local wording or formatting fix, inspect the affected contract and a relevant example first; a full comparison is not mandatory. Use the escalation criteria below when choosing evaluation depth.

## What To Test

Use a small set that covers:

- a straightforward case
- a realistic messy case
- an ambiguous case
- a near-boundary case where the prompt may become too rigid or too vague

Good tests sound like real users. They should include the kind of messy wording, incomplete context, and uneven specificity that real prompts will face.

## What To Look For

Check whether the prompt:

- establishes the right role and audience
- uses concise wording without losing critical context
- defines important concepts clearly enough
- converges toward the intended output
- leaves the right amount of freedom
- avoids decorative or redundant instructions

## Before/After Comparison

When repairing an existing prompt, compare:

- the old prompt output
- the revised prompt output
- where the revised version improved
- what it may have accidentally worsened

Run old/new or with/without comparisons in separate fresh contexts, with the same model, settings, task inputs, and tool access. A context that already read the target prompt is not an unassisted baseline. Keep grading criteria consistent and outside the raw task input. Record which comparisons actually ran; an editorial review alone supports a design judgment, not a measured behavioral improvement.

Do not treat "different" as automatically "better". Look for clearer reasoning, better adherence to the intended audience, and less noise.

## Escalate Only When Needed

Move from light evaluation to a more structured comparison when:

- the prompt will be reused heavily
- the prompt influences high-stakes outputs
- the prompt competes with other prompts or skills
- small wording changes have large downstream effects

In those cases, add a clearer rubric or do a blind comparison. Otherwise, keep the loop fast and practical.
