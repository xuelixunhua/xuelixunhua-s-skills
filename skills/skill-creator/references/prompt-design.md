# Prompt Design Guide

## Prompt = Packaged Method

A prompt is a portable method. It should help another person or agent invoke the right reasoning quickly, without needing your full background context.

## Core Principles

### 1. Define Both Sides

Make it clear who the model is and who it serves.

- Bad: "Write something persuasive."
- Better: "You are a product strategist writing for a skeptical executive who wants a concise recommendation."

### 2. Use The Fewest Accurate Words

Prompts are not essays. Remove wording that does not change the model's behavior.

Ask of every sentence:

- Does this reduce ambiguity?
- Does this set a real constraint?
- Does this improve the quality bar?

If not, cut it.

### 3. Use Explicit Concepts And Definitions

Name the important ideas precisely. If a term has a special meaning in this task, define it.

Precision is especially important for:

- domain jargon
- evaluation criteria
- structured outputs
- quality adjectives like "sharp", "professional", or "strategic"

### 4. Provide Enough Context

Useful context usually includes:

- the situation
- the current state
- the goal
- important constraints
- degrees of freedom

The aim is not to tell the whole story. The aim is to create the minimum context that lets the model reason correctly.

### 5. Decompose Complex Work

When the task is cognitively dense, split it into sub-problems. This narrows attention and reduces shallow, blended answers.

Examples:

- analyze first, then rewrite
- summarize first, then critique
- list options first, then choose

## Prompt Repair Checklist

When improving a prompt, look for:

- vague role definition
- missing audience or service target
- missing success criteria
- undefined key terms
- too much decorative language
- brittle step-by-step instructions
- over-specified output shape
- under-specified output shape

## Tighten Without Overconstraining

Good prompts converge attention without crushing judgment.

- Add strict structure when output shape matters
- Add heuristics when reasoning quality matters
- Add steps only when sequence matters

If you explain why a rule matters, the model can often generalize better than if you only impose the rule.

## When To Upgrade A Prompt To A Skill

Upgrade from prompt to skill when:

- the same method keeps recurring
- the task should trigger automatically from many user phrasings
- the work needs bundled resources
- the method is becoming a durable capability rather than a single phrasing pattern

If none of those are true yet, a good prompt may be the right final artifact.
