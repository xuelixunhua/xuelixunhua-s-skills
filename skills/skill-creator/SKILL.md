---
name: skill-creator
description: Create, repair, and optimize reusable prompts, skills, and adjacent harness instructions. Use when users want to turn a workflow or methodology into a prompt, decide whether something should become a skill, improve an existing prompt or SKILL.md, package reusable agent behavior, or strengthen skill triggering and quality instead of solving a one-off task.
---

# Prompt / Skill Creator

This skill helps Codex package reusable agent behavior. Treat prompt writing and skill writing as harness design, not as document filling. Default to the smallest artifact that will reliably solve the recurring problem.

## Mission

Use this skill when the user wants to:

- create a new prompt, skill, or harness rule
- repair an existing prompt or skill
- decide whether something should be a prompt, skill, or global rule
- turn a personal method into a reusable artifact
- improve trigger quality, structure, or reuse

If the user only needs a one-off answer, solve the task directly instead of creating a reusable artifact.

## Start With Packaging, Not Writing

Before drafting anything, identify the reusable unit:

1. What exactly should become reusable: a wording pattern, a workflow, a capability, or a rule?
2. How often will this recur?
3. Does it need automatic triggering?
4. Does it need scripts, references, assets, or evaluation infrastructure?
5. Is it global and stable enough to belong in `AGENTS.md` or `CLAUDE.md` instead?

Use the smallest container that preserves the method:

- Direct answer: for one-off work with no reuse value
- Prompt: for a reusable way of asking or framing work that can travel as text
- Skill: for a reusable capability that needs triggering, resources, or a durable agent philosophy
- `AGENTS.md` or `CLAUDE.md`: for global, stable, cross-task rules

Do not default to creating a new skill. First ask whether the work should be absorbed into an existing skill or stay as a prompt. See `references/artifact-packaging.md` when you need a sharper boundary check.

## Core Design Philosophy

### Prompt = Packaged Methodology

A good prompt packages a method so another person can reuse it quickly. Your job is not to make it sound elaborate. Your job is to make the method easy to invoke and hard to misunderstand.

When creating or repairing a prompt, make sure it does the following:

1. Define both sides of the conversation: who the model is and who it serves
2. Use the fewest words that still preserve meaning
3. Use precise concepts and explicit definitions where ambiguity would hurt
4. Provide enough context: situation, current state, goal, and room to maneuver
5. Break complex work into smaller sub-problems when focus matters

Prompt writing is convergence work. Models are naturally expansive, so the prompt should concentrate attention on the right problem, the right constraints, and the right output.

### Skill = Classification + Triggering + Philosophy

A good skill is not just a long instruction file. It is a reusable capability with a boundary and a trigger surface.

- Classification: define the capability boundary at the right granularity
- Triggering: make sure Codex can recognize when the skill should activate
- Philosophy: teach the agent how to think, not just what buttons to press

Use this formula when designing or revising a skill:

`high-quality skill = strategy philosophy + minimum complete toolkit + necessary facts`

Two broad skill shapes are common:

- Fixed workflow: repeatable jobs with a stable sequence
- Agent framework: broader capability prompts that guide strategy across many situations

Most good skills are hybrids, but one of these should dominate.

### Strategy Philosophy Comes First

The most important part of a strong skill is the reasoning pattern. Write the target and the thought process before you write detailed steps.

At minimum, the philosophy should help the agent:

1. Define the success criteria
2. Choose the best starting point
3. Treat intermediate results as evidence and correct course early
4. Stop when the success criteria are met

Only add rigid step-by-step procedures when the work is fragile, order-dependent, or safety-critical. Otherwise, prefer goals, heuristics, and decision points. See `references/workflows.md` for patterns.

### Minimum Complete Toolkit

Bundle the smallest set of tools and resources that makes the capability reliable:

- `scripts/` for repeated deterministic work
- `references/` for detailed facts, schemas, or domain notes
- `assets/` for templates and materials used in outputs

Do not add resources just because the folders exist. Every bundled file should reduce repeated work or improve reliability.

### Necessary Facts

Add facts that the model is likely to forget, underuse, or mis-prioritize:

- preferred starting points
- domain terminology
- hidden constraints
- quality bars
- safety boundaries

Facts are there to awaken useful knowledge, not to dump everything you know.

## Prompt Workflow

When the user wants a prompt, repaired prompt, or prompt library item:

1. Identify the job to be done, intended user, and failure modes
2. Decide whether the result should be a one-shot prompt, a reusable prompt template, or a prompt family with variants
3. Draft the prompt using the five prompt principles above
4. Remove language that is decorative, redundant, or overly rigid
5. Tighten the output contract only as much as the task actually needs
6. Provide 2-5 realistic test inputs that pressure the weak edges

If the user wants a durable prompt artifact on disk, scaffold it with `scripts/init_prompt.py`, then fill in `PROMPT.md` and `TEST_INPUTS.md` instead of starting from a blank file.

When repairing a prompt, diagnose before rewriting. Common issues include:

- vague role or service target
- too much wording and too little signal
- missing context or success criteria
- undefined key concepts
- over-constrained steps that block model judgment
- format instructions that are either too loose or unnecessarily rigid

If useful, present prompt work in this shape:

1. what the prompt is trying to achieve
2. what is weak in the current version
3. revised prompt
4. why the changes help
5. test prompts for validation

For a deeper prompt checklist, see `references/prompt-design.md`.

For a lightweight review loop, see `references/prompt-evaluation.md`.

## Skill Workflow

When the user wants a new skill or an existing skill revised:

1. Capture intent from the conversation before interviewing the user again
2. Decide whether a new skill should exist at all
3. Define the skill boundary and nearby cases it should absorb
4. Decide whether it is mainly a fixed workflow, an agent framework, or a hybrid
5. Write the strategy philosophy before the detailed workflow
6. Add only the minimum complete toolkit and the necessary facts
7. Write a trigger-aware `description` that says both what the skill does and when to use it
8. Keep `SKILL.md` lean and push detailed material into `references/`
9. Validate and iterate on realistic prompts

When the user is editing an existing skill, inspect these separately:

- `name`: keep stable unless there is a strong reason to rename
- `description`: improve triggering, boundaries, and examples of when to use
- `SKILL.md` body: improve philosophy, workflow, and resource routing
- bundled resources: add only when repeated work proves they are needed

Do not solve undertriggering by making the description vague or universal. Make it broad enough to catch real adjacent phrasings, but still defend the category boundary.

## Description and Trigger Quality

The frontmatter `description` is the primary trigger surface. It should include:

- what capability the skill provides
- the requests or contexts that should activate it
- nearby phrasing that should still count
- enough specificity to beat near-miss skills

Prefer realistic request language over abstract labels. If needed, generate trigger evals and refine from evidence rather than instinct.

## Editing Mode

When the user gives you an existing prompt or skill, go into editing mode instead of greenfield mode.

For prompts:

- identify the preserved core
- diagnose the weak spots
- rewrite with less noise and better structure
- explain the delta

For skills:

- preserve the durable identity
- improve the classification boundary
- improve triggering
- upgrade the philosophy before adding procedural weight
- only then revisit evals, scripts, and references

## Evaluation and Iteration

Use the lightest evaluation loop that matches the stakes:

- Prompts: realistic example prompts, before/after comparison, and user review
- Skills: realistic trigger prompts, artifact inspection, validation scripts, and if needed the heavier benchmark workflow

Do not overfit to a few examples. Generalize from feedback and remove instructions that are not pulling their weight.

When the environment supports it and the user wants rigor, you may still use the full skill evaluation loop:

- generate realistic eval prompts
- run with-skill and baseline comparisons
- inspect outputs qualitatively
- add quantitative checks only where the output is objectively verifiable
- iterate until improvements are real

## Creating New Skills

When the packaging decision says "skill":

1. decide the skill name and destination
2. run `scripts/init_skill.py` to scaffold the folder
3. replace the template with a philosophy-first `SKILL.md`
4. remove any placeholder resources that are not needed
5. run `scripts/quick_validate.py` before handing it off

The scaffolder is there to save time, not to think for you. The template still needs a real boundary, trigger surface, and strategy philosophy.

## Creating New Prompts

When the packaging decision says "prompt":

1. decide the prompt name and destination
2. run `scripts/init_prompt.py` to scaffold the prompt folder
3. replace the template with a concise, method-preserving prompt
4. fill in `TEST_INPUTS.md` with realistic cases
5. run a lightweight prompt eval loop before treating it as reusable

Prompt scaffolding is for reuse, not decoration. Keep the stored artifact lean enough that someone else could understand and apply it quickly.

## Using References

Read the reference files selectively:

- `references/artifact-packaging.md` for prompt vs skill vs global-rule decisions
- `references/prompt-design.md` for prompt principles and prompt repair
- `references/prompt-evaluation.md` for lightweight prompt validation
- `references/workflows.md` for philosophy-first workflow patterns
- `references/output-patterns.md` for useful response shapes when presenting prompt or skill work

## Working Style

- Prefer concise, high-signal language
- Explain why before adding strict rules
- Write goals before steps
- Keep artifacts small enough to stay legible
- Prefer merging into the right existing category over creating another thin skill
- Treat reusable prompts and skills as harness components, not just text outputs
