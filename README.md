# xuelixunhua's skills

Personal Codex skills maintained by xuelixunhua.

## Recent Updates

- 2026-09-06: refreshed `content-master`, `skill-creator`, `web-access`, and `chief-of-staff-collaboration` from the maintained local Codex copies. Content work now has clearer analysis/writing handoffs, selective thinking-toolbox reading, refined references, and concise decision updates. Skill creation preserves strategy philosophy and uses proportional validation; web access prefers native tools with a Windows fallback; collaboration adds scoped preference handling. Decision-update consistency remains a known behavioral limitation, not a fully passed guarantee.
- 2026-09-06: corrected the `skill-creator` source to the Personal Codex directory and added selective sync, preview, path checks, and public-file exclusions. Local configuration, private site notes, session-linked cases, and generated eval results are not exported.
- 2026-07-26: added `chief-of-staff-collaboration`, a chief-of-staff-style collaboration skill for delegated judgment, multi-stage execution, authorization boundaries, verified closure, and sensitive organizational interaction. It includes an opt-in installer for the matching global `AGENTS.md` route.
- 2026-07-12: added `pdf-to-markdown-pipeline`, an evidence-first PDF-to-Markdown workflow with extraction, structure building, strict audits, review queues, and source-grounded backfills.
- 2026-06-22: refreshed `llm-wiki-workspace` with the vertical knowledge-base branch, including three-layer material handling and first-layer viewpoint index entries for sources that need callable conclusions without becoming standalone notes.
- 2026-06-13: added `creator-content-knowledge-pipeline`, a creator/content-to-knowledge-base pipeline skill for turning Bilibili UPs, podcasts, courses, or video series into vertical knowledge-base products and reusable production engines.
- 2026-06-05: refreshed `content-master` from the local Codex skill. The thinking-analysis module is now a problem-first dispatcher backed by `references/cross-disciplinary-thinking-toolbox.md`, with additional eval prompts for career choice, procrastination/system analysis, and industry-opportunity judgment.
- 2026-06-05: refreshed `skill-creator` from the local Agents skill. It now adds a harness audit before editing reference files, separating the control plane from the knowledge plane.

## Skills

| Skill | Source on maintainer machine | Notes |
| --- | --- | --- |
| `bggg-skill-taotie` | `~/.codex/skills/bggg-skill-taotie` | Skill evolution and skill-merging workflow. |
| `chief-of-staff-collaboration` | `~/.codex/skills/chief-of-staff-collaboration` | Delegated judgment and continued execution with explicit intent, reality, authorization, closure, and relationship boundaries. |
| `content-master` | `~/.codex/skills/content-master` | Content thinking, note processing, WeChat/article writing, and problem-first thinking analysis. |
| `creator-content-knowledge-pipeline` | `~/.codex/skills/creator-content-knowledge-pipeline` | Creator/video-to-knowledge-base pipeline for Layer 3 vertical knowledge products and Layer 4 production engines. |
| `llm-wiki-workspace` | `~/.codex/skills/llm-wiki-workspace` | Markdown-first LLM wiki plus vertical/domain knowledge-base harness. |
| `primitive-thinking` | `~/.codex/skills/primitive-thinking` | Primitive, niche opportunity, and frugal stack thinking. |
| `pdf-to-markdown-pipeline` | `~/.codex/skills/pdf-to-markdown-pipeline` | Evidence-first PDF conversion into reusable Markdown and structured artifacts. |
| `research-synthesis` | `~/.codex/skills/research-synthesis` | Investment research synthesis and framework notes. |
| `web-access` | `~/.codex/skills/web-access` | Browser/web access workflow and helper scripts. |
| `skill-creator` | `~/.codex/skills/skill-creator` | Personal skill and prompt design, strategy philosophy, selective resources, UI metadata, and proportional validation. |

## Repository Layout

```text
skills/
  chief-of-staff-collaboration/
    SKILL.md
    references/
    scripts/install-global-agents-route.ps1
  content-master/
    SKILL.md
    thinking-analysis.md
    references/cross-disciplinary-thinking-toolbox.md
    evals/evals.json
  creator-content-knowledge-pipeline/
    SKILL.md
    references/
    assets/
  pdf-to-markdown-pipeline/
    SKILL.md
    references/pdf-to-markdown-method.md
    scripts/
  skill-creator/
    SKILL.md
    references/
    scripts/
```

## Install Into Codex

Clone this repository, then run:

```powershell
.\scripts\install-codex.ps1
```

By default this installs all folders under `skills/` into:

```text
$HOME\.codex\skills
```

Install selected skills only:

```powershell
.\scripts\install-codex.ps1 -Skills content-master,research-synthesis
```

Overwrite existing local copies:

```powershell
.\scripts\install-codex.ps1 -Force
```

Restart Codex after installing or updating skills.

### Additional setup for `chief-of-staff-collaboration`

This skill uses its `description` for native implicit invocation and adds a global `AGENTS.md` route to make the intended classification persistent across tasks. After installing the skill, preview the global-route change:

```powershell
.\skills\chief-of-staff-collaboration\scripts\install-global-agents-route.ps1 -WhatIf
```

Then install it:

```powershell
.\skills\chief-of-staff-collaboration\scripts\install-global-agents-route.ps1
```

The helper targets `$HOME\.codex\AGENTS.md`, preserves existing guidance, creates a timestamped backup before writing, and uses managed markers so repeated runs update one block instead of appending duplicates. For manual installation, read `skills/chief-of-staff-collaboration/references/global-agents-routing.md`.

## Maintainer Sync

On the maintainer machine, refresh this repository from local skill sources:

```powershell
.\scripts\sync-from-local.ps1
```

The publish whitelist is `manifest.json`; all entries use the maintained Personal copies in `~/.codex/skills`. Do not substitute the bundled `.system` copy for `skill-creator`.

Preview or refresh only selected skills:

```powershell
.\scripts\sync-from-local.ps1 -Skills content-master,skill-creator,web-access,chief-of-staff-collaboration -WhatIf
.\scripts\sync-from-local.ps1 -Skills content-master,skill-creator,web-access,chief-of-staff-collaboration
```

Sync replaces the selected repository copies, including removal of obsolete files. Start from a clean branch or worktree and preserve unrelated local edits. Missing sources, unknown names, invalid mappings, and linked directories abort before replacement. `-SourceRoot` can point at a disposable source tree for testing.

Review reusable eval inputs separately from generated evidence: the trigger runner observes Skill reads and stops early; it does not grade finished answers. Local run outputs and session-linked regression cases are excluded. Browser workflows still need live acceptance in their target environment.

Run the packaging regressions with Python and PowerShell available:

```powershell
python -B -m unittest discover -s scripts/tests
python -B skills/skill-creator/evals/test_tools.py
```

The skill-creator helper tests also require PyYAML. These checks use disposable destinations and do not update installed skills or global instructions.

`web-access` compatibility: `/new` and `/navigate` now accept URLs in POST bodies; see `skills/web-access/references/migration-2.5.3.md`. The local version no longer exposes `/type` and `/press`; use the native browser controls or the documented `/eval` interface. Windows helper entry points are `.mjs` files instead of the previous `.sh` wrappers.

Then review and commit:

```powershell
git status
git add .
git commit -m "Update skills"
git push
```

## What Is Not Included

This repository intentionally excludes:

- Codex system skills from `~/.codex/skills/.system`
- plugin caches, vendor imports, session databases, logs, auth files, and generated runtime state
- old archived local skills that are no longer maintained
- third-party proprietary skill bundles unless their license clearly allows redistribution
