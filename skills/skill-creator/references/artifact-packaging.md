# Artifact Packaging Guide

## Smallest Useful Container

Default to the smallest artifact that preserves the method:

- Direct answer: for one-off tasks with no reuse value
- Prompt: for reusable wording or framing that can travel as text
- Skill: for reusable capabilities that need triggering, resources, or a durable agent philosophy
- `AGENTS.md` or `CLAUDE.md`: for global, stable, cross-task rules

Do not create a new skill just because something is useful. Reusable does not automatically mean "skill".

## Decision Questions

Ask these before creating anything:

1. What exactly is being reused?
2. How often will it recur?
3. Does it need automatic triggering?
4. Does it need bundled scripts, references, or assets?
5. Is it global policy, domain capability, or a single tactic?
6. Could an existing skill absorb it cleanly?

## Quick Comparison

| Container | Best for | Signals | Avoid when |
|-----------|----------|---------|------------|
| Direct answer | One-off help | No durable method is needed | The user clearly wants reuse |
| Prompt | Reusable framing or method | Copy-paste use is enough; manual invocation is acceptable | The work needs auto-triggering or bundled resources |
| Skill | Reusable capability | Needs a trigger surface, scripts, references, assets, or a durable philosophy | The scope is too narrow or should merge into an existing skill |
| `AGENTS.md` / `CLAUDE.md` | Global rules | Stable across many domains and tasks | The rule only matters inside one capability area |

## Prompt Or Skill?

Choose a prompt when:

- the main value is wording, structure, or framing
- the user will invoke it manually
- there is no need for bundled files or tool-routing
- the capability is still too narrow or experimental for a standalone skill

Choose a skill when:

- the capability should trigger from many related phrasings
- the agent benefits from a reusable boundary and strategy philosophy
- the work repeatedly requires the same scripts, templates, or reference notes
- the capability will be used across many tasks over time

## New Skill Or Existing Skill?

Prefer improving an existing skill when:

- the new request is a branch or sub-scenario of an established capability
- the existing skill can absorb the case without becoming incoherent
- adding a new skill would mainly duplicate trigger language

Prefer a new skill when:

- the boundary is genuinely different
- the trigger surface would otherwise become muddy
- the capability has a distinct philosophy, toolkit, or ownership

## Granularity Rule

Use the minimum number of skills that preserves clear classification.

- Too coarse: unrelated scenarios collide
- Too fine: trigger quality drops, maintenance expands, and the catalog becomes noisy

When in doubt, ask whether the scenario is better represented as:

- a branch inside the existing skill
- a reusable prompt inside the existing workflow
- or a truly separate capability
