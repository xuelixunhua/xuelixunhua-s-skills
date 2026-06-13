# xuelixunhua's skills

Personal Codex skills maintained by xuelixunhua.

## Recent Updates

- 2026-06-13: added `creator-content-knowledge-pipeline`, a creator/content-to-knowledge-base pipeline skill for turning Bilibili UPs, podcasts, courses, or video series into vertical knowledge-base products and reusable production engines.
- 2026-06-05: refreshed `content-master` from the local Codex skill. The thinking-analysis module is now a problem-first dispatcher backed by `references/cross-disciplinary-thinking-toolbox.md`, with additional eval prompts for career choice, procrastination/system analysis, and industry-opportunity judgment.
- 2026-06-05: refreshed `skill-creator` from the local Agents skill. It now adds a harness audit before editing reference files, separating the control plane from the knowledge plane.

## Skills

| Skill | Source on maintainer machine | Notes |
| --- | --- | --- |
| `bggg-skill-taotie` | `~/.codex/skills/bggg-skill-taotie` | Skill evolution and skill-merging workflow. |
| `content-master` | `~/.codex/skills/content-master` | Content thinking, note processing, WeChat/article writing, and problem-first thinking analysis. |
| `creator-content-knowledge-pipeline` | `~/.codex/skills/creator-content-knowledge-pipeline` | Creator/video-to-knowledge-base pipeline for Layer 3 vertical knowledge products and Layer 4 production engines. |
| `llm-wiki-workspace` | `~/.codex/skills/llm-wiki-workspace` | Markdown-first long-lived LLM wiki workspace. |
| `primitive-thinking` | `~/.codex/skills/primitive-thinking` | Primitive, niche opportunity, and frugal stack thinking. |
| `research-synthesis` | `~/.codex/skills/research-synthesis` | Investment research synthesis and framework notes. |
| `web-access` | `~/.codex/skills/web-access` | Browser/web access workflow and helper scripts. |
| `skill-creator` | `~/.agents/skills/skill-creator` | Prompt and skill design workflow, including harness/control-plane audits. |

## Repository Layout

```text
skills/
  content-master/
    SKILL.md
    thinking-analysis.md
    references/cross-disciplinary-thinking-toolbox.md
    evals/evals.json
  creator-content-knowledge-pipeline/
    SKILL.md
    references/
    assets/
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

## Maintainer Sync

On the maintainer machine, refresh this repository from local skill sources:

```powershell
.\scripts\sync-from-local.ps1
```

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
