---
name: skill-creator
description: Create, update, simplify, and validate reusable skills and prompts. Use to turn a recurring method into a skill, revise SKILL.md, preserve strategy philosophy while compressing instructions, improve triggers or bundled tools, or choose between a prompt, skill, and scoped project rules. One-off writing and ordinary task execution do not need this skill.
---

# Skill Creator

This personal version owns design, construction, and validation. Preserve its established name, path, and Personal UI identity. The bundled system version is an optional read-only conventions reference, never an automatic handoff or a copy to edit.

## 1. Choose What To Preserve And Package

Start from the user's intent and existing artifacts. Identify the recurring method, who it serves, its success criteria, and the principles or constraints that must survive. Reuse conversation context before asking for missing information.

Choose the smallest container that preserves the method:

| Container | Use |
| --- | --- |
| Direct answer | One-off work without a reusable capability to preserve |
| Prompt | A portable method or framing that can be invoked as text |
| Skill | A recurring capability with a trigger boundary, strategy philosophy, or bundled resources |
| Scoped instructions | Stable rules for their actual scope: user-wide, repository, or subdirectory; place `AGENTS.md` or the host equivalent accordingly |

Prefer a coherent extension of an existing skill over a new thin or overlapping one. Keep distinct capabilities separate when combining them would blur their triggers or decisions. A reusable file, script, or template can also belong in an existing capability without becoming another skill.

## 2. Strategy Philosophy Comes First

`Skill = classification + triggering + philosophy`

`High-quality skill = strategy philosophy + minimum complete toolkit + necessary facts`

Strategy philosophy determines the skill's direction: what it optimizes for, how it makes tradeoffs, and how it adapts when the obvious path fails. It governs the choice of workflow, tools, and evaluation criteria. Preserve this core when compressing a skill; remove repeated wording without erasing the user's values or domain judgment.

Write a compact, task-specific philosophy before detailed procedures. It should guide:

1. **Direction and success:** whose problem is being solved, what a good result achieves, and which qualities matter most.
2. **Priorities and boundaries:** what must hold, what can vary, and how to choose when goals conflict.
3. **Starting point and route:** which evidence or action is most informative, and when another route is appropriate.
4. **Feedback and correction:** how intermediate results change the approach or invalidate an assumption.
5. **Completion:** what evidence is sufficient to finish and what unresolved condition requires further work.

These are design questions, not mandatory headings in every generated skill. State the domain's actual decisions instead of copying generic slogans. A fixed workflow still needs its purpose and governing judgment; an agent framework needs more guidance on choosing among approaches. Most skills combine both.

Match constraint strength to the work: goals and heuristics for variable judgment, preferred patterns for stable but adaptable work, and explicit sequences or scripts for fragile, order-dependent operations. Explain the reason for strict rules. Stronger models still need private facts, user preferences, tool coordination, and real boundaries; do not delete these merely because no benchmark proves their value.

## 3. Build Or Revise

1. **Inspect before changing.** For an existing artifact, preserve its identity, philosophy, user-locked content, and useful resources. Diagnose the failure or repetition; avoid rebuilding from a blank template.
2. **Define the capability boundary.** Keep the name stable. Front-load the main job and realistic trigger language in `description`, then clarify near misses. Broaden adjacent phrasing without making the skill universal. Distinguish same-name copies by path and UI identity.
3. **Express the method once.** Let the philosophy guide one main workflow with only necessary branches. For prompts, preserve role and audience, precise concepts, relevant context, and the output contract; decompose only where it improves focus.
4. **Put resources in their proper place.** Keep reference selection, tool routing, and orchestration in `SKILL.md`. References carry facts, examples, schemas, and deep method detail. Fix unclear routing before adding more reference material.
5. **Implement the smallest complete artifact.** Use the helpers below when creating files; edit existing artifacts in place. Add scripts for repeated deterministic work, assets for output templates, and facts the model would otherwise miss or mis-prioritize.
6. **Validate and explain the change.** Use the appropriate checks below. Report what was preserved, what changed, the evidence obtained, and any remaining uncertainty. Explain structure only when it helps the user understand or maintain the result.

Compress by merging duplicate rules, removing generic reminders, and loading detail on demand. Do not trade away useful definitions, philosophy, or exceptions to meet a line quota. Revisit inherited constraints after meaningful model upgrades and retain the smallest intervention that addresses an observed failure.

## 4. Validate In Proportion To The Change

| Change | Sufficient starting check | Escalate when |
| --- | --- | --- |
| Wording, paths, or metadata | Inspect the diff; check structure and affected references/configuration | Meaning, routing, or behavior also changes |
| Scripts or file operations | Run representative inputs and relevant failure/regression cases in a temporary directory | A dependency or integration remains uncertain |
| Philosophy, triggers, or workflow | Review preservation of intent; examine core, messy, and near-miss cases against explicit success criteria | Actual trigger behavior or an improvement claim needs independent evidence |

Use `scripts/quick_validate.py` for structural checks. Add `--ready` before delivery to check scaffold markers and literal bundled file references in the entry file. This is not a full resource audit or proof of good model behavior; inspect examples, computed paths, and changed resource content separately. Do not run destructive scripts merely to satisfy a check.

For behavioral claims, compare representative tasks in fresh, separate contexts using the same model, settings, inputs, and tool access. A conversation that has already read the skill is not a no-skill baseline. Use with/without-skill or old/new comparisons as appropriate; a subtraction test can isolate a disputed rule. Keep grading criteria consistent without leaking expected answers or suspected fixes into the task input. Fresh runs or subagents are optional when available and proportionate, not a prerequisite for every edit.

Distinguish **structural checks**, **script checks**, **scenario review**, and **independent behavioral evaluation** in the evidence. If a fresh evaluation is unavailable or disproportionate, finish the authorized work and describe improvement as a design judgment until tested. Do not invent a baseline or claim success from a preferred-looking output.

Keep durable eval cases outside runtime instructions. Use verifiable checks where possible, inspect quality where judgment matters, and include regression cases. Stop once acceptance and relevant checks are satisfied; expand testing only for new failures or unresolved concerns.

## 5. Loading And Tooling

The host first exposes skill metadata, possibly shortening descriptions. The selected `SKILL.md` carries direction, decisions, and resource routing. Load references, scripts, assets, and evals only as needed. Link required resources directly; avoid reference chains. Around 500 lines is a review signal, not a target. Do not create empty resource folders or extra README, changelog, or installation files without a concrete need.

| Helper | Purpose |
| --- | --- |
| `scripts/init_skill.py` | Create a lowercase hyphenated skill folder, core scaffold, UI metadata, and selected resource folders; replace placeholders before delivery |
| `scripts/init_prompt.py` | Create `PROMPT.md` and `TEST_INPUTS.md` when a reusable prompt is requested on disk |
| `scripts/generate_openai_yaml.py` | Create or update optional UI metadata in UTF-8, preserving unmodified configuration values |
| `scripts/quick_validate.py` | Structural checks; optional `--ready` entry-file checks; neither mode evaluates model behavior |

Run these helpers with a Python environment that has PyYAML. Resolve filesystem paths in the host environment. For new skills, choose name and destination, select only justified resources, run the scaffolder, fill the method, and validate. UI metadata is optional for hand-authored skills; the scaffolder supplies it for convenience.

When changing the helpers, run `evals/test_tools.py` for focused file/configuration regressions. It uses temporary cases under the working directory's `work/` and does not call a model.

Read references selectively:

| Reference | Read when |
| --- | --- |
| `references/artifact-packaging.md` | Prompt, skill, and scoped-rule boundaries need a closer decision |
| `references/prompt-design.md` | A reusable prompt needs detailed design or diagnosis |
| `references/prompt-evaluation.md` | Prompt behavior needs a lightweight comparison or grading rubric |
| `references/workflows.md` | Translating philosophy into adaptive, sequential, or branching workflows |
| `references/output-patterns.md` | A presentation pattern would help explain the result; templates are optional |
| `references/openai_yaml.md` | Creating or updating UI fields, invocation policy, or tool dependencies |
