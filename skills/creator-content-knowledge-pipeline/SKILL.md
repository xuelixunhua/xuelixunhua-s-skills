---
name: creator-content-knowledge-pipeline
description: Turn a creator, channel, Bilibili UP, podcast, course, or video series into a maintainable vertical knowledge base. Use when the user asks to download or collect creator content, transcribe audio/video, classify episodes, build route/topic notes, create a GitHub/Notion/local knowledge repo, or productize this workflow into a reusable content knowledge pipeline. Especially relevant to B站视频、UP主内容库、林超类领域视频、虎牙青年 Plus、从视频到转写到总结、垂直知识库、知识资产、第三层知识库产品、第四层生产引擎.
---

# Creator Content Knowledge Pipeline

## Mission

Turn a creator's continuous content into reusable knowledge assets.

This skill is for the full pipeline from content source to durable knowledge product:

```text
creator / channel / series
-> source inventory
-> audio or transcript acquisition
-> transcription
-> clean index
-> classification
-> reusable notes
-> knowledge base or public repo
-> cleanup and maintenance loop
```

The goal is not "summarize videos." The goal is to turn high-signal creator output into a maintainable vertical knowledge base that can support research, writing, travel, product thinking, and future AI retrieval.

## Product Target

Preserve the third-layer and fourth-layer product logic:

- **Layer 3: vertical knowledge base product.** Build field-specific knowledge assets such as travel geography, business analysis, AI products, investment research, history, or creator-specific libraries. This is the outward-facing product.
- **Layer 4: production engine.** Build the reusable workflow, skill, templates, and scripts that repeatedly produce Layer 3 assets. This is the internal operating system.

When making choices, prefer decisions that strengthen both layers: a cleaner knowledge output now, and a more reusable production pattern next time.

## Success Criteria

- Defines the target content scope clearly: creator, platform, series, date range, playlist, topic, or URL list.
- Produces a durable local workspace with stable folders, indexes, logs, and outputs.
- Uses the lightest reliable acquisition path: command line or API first, browser automation only when the page requires login, dynamic rendering, or manual workflows.
- Converts raw material into structured notes, not generic summaries.
- Separates private/raw materials from public outputs.
- Leaves behind an update path so the knowledge base can absorb future content.
- Cleans or flags large intermediates such as audio/video after they are no longer needed.

## Trigger Surface

Use this skill when the user asks to:

- "把某个 B 站 UP 主的视频做成知识库"
- "从 B 站下载视频、转写、总结、发布"
- "整理林超/虎牙青年 Plus/某个创作者的系列内容"
- "把一批视频变成笔记、索引、课程大纲、GitHub 仓库、Notion 知识库"
- "做一个垂直知识库产品"
- "把下载、转写、分类、总结这套流程做成 Skill"
- "把创作者内容资产化、产品化、长期维护"

Do not use this skill for a one-off short video summary unless the user also wants a reusable index, knowledge base, productizable workflow, or repeatable pipeline.

## Strategy Philosophy

Think like an operator building a knowledge product, not like a summarizer.

1. **Start from the product shape.** Decide whether the output is a private research folder, a public GitHub repo, a Notion/Obsidian wiki, a series of articles, a course outline, or a dataset.
2. **Inventory before interpretation.** Build a source table before writing conclusions. Missing or duplicated source items corrupt the downstream knowledge base.
3. **Keep raw, processed, and public layers separate.** Audio/video/transcripts are working material; cleaned notes and indexes are products.
4. **Classify before deep writing.** A creator's value usually appears through series, themes, recurring questions, and worldview, not isolated episode summaries.
5. **Write reusable notes.** The note should answer "what can this teach later?" rather than "what happened in this episode?"
6. **Treat every run as a pipeline rehearsal.** Capture enough structure that the next creator or field becomes faster.

## Tool Delegation

This skill orchestrates the pipeline. It does not replace lower-level tools.

- Use command line, scripts, APIs, or existing local tools for deterministic work: downloads, file moves, CSV/JSON cleanup, checksums, indexing, line counts, and Git.
- Use `web-access` for internet/search/browser tasks, especially Bilibili pages, Tongyi Tingwu, login state, dynamic pages, upload/download actions, and batch deletion in web apps.
- If the current environment provides a reliable built-in browser or Computer Use capability, it can be used as the browser backend. Prefer the backend that has the required login state and can complete the task with the least friction.
- Use `content-master` for classification, note restructuring, knowledge crystallization, public-facing README text, and article-grade expression.
- Use GitHub tooling or local `git` when the output is a public repo or versioned knowledge base.

Default rule: command line/API first; browser automation for logged-in or dynamic web tasks; content skill for thinking and writing.

## Workflow

Open `references/pipeline-workflow.md` for the detailed phase checklist when running a real project.

The compact workflow is:

1. **Define scope and output product**
   - source platform, creator, series, date range, target public/private boundary
   - desired output: wiki, repo, article set, dataset, prompt library, product sample

2. **Create workspace**
   - keep `raw/`, `audio/`, `transcripts/`, `data/`, `outputs/`, `logs/`, and `tmp/` conceptually separate
   - if the user already has a mature folder, preserve it and add only missing layers

3. **Inventory sources**
   - collect title, URL/BV ID, date, duration, play count if useful, series/category, transcript path, status
   - verify counts against the platform before claiming completeness

4. **Acquire audio or transcripts**
   - prefer audio-only when transcription is the goal
   - keep logs of failed downloads or unavailable items
   - do not publish raw audio/video by default

5. **Transcribe**
   - use the available transcription provider or existing user workflow
   - verify every source has a transcript or an explicit failure status
   - store transcripts in a non-public working layer unless the user explicitly wants otherwise and rights are clear

6. **Classify**
   - classify by series, route, topic, knowledge theme, audience use case, and long-term product value
   - build a clean public-safe index that removes local paths and raw-system identifiers

7. **Synthesize**
   - write master frameworks, route/topic notes, source cards, and reusable reading paths
   - avoid episode-by-episode digests unless the user needs them

8. **Package**
   - choose the public product shape: GitHub repo, local wiki, Notion export, article draft set, or dataset
   - write README/entrypoint explaining creator, interpretation, content map, maintenance plan, and source boundary

9. **Clean and maintain**
   - delete or archive large intermediates after transcripts and notes are verified
   - record how to update new episodes
   - keep product layer clean and reusable

## Productization Guidance

Open `references/product-strategy.md` when the user asks about monetization, product positioning, third/fourth layer strategy, vertical knowledge products, or whether the pipeline is worth building.

Default stance:

- Do not compete as a generic video summarizer.
- Compete as a vertical knowledge-base producer and production engine.
- Start with domains the user already follows deeply.
- Produce public samples before building a SaaS.
- Let repeated manual runs reveal what deserves scripting.

## Output Guidance

When finishing a pipeline run, report:

- what was collected
- what was transcribed
- what was classified
- what knowledge artifacts were created
- what was intentionally not published
- what intermediates were cleaned
- how to update the project next time

When designing a new project, produce:

- product target
- workspace structure
- source inventory plan
- transformation pipeline
- public/private boundary
- maintenance loop
- first small test run

## Resource Map

- `references/pipeline-workflow.md`: detailed execution checklist for creator-to-knowledge projects.
- `references/product-strategy.md`: third-layer and fourth-layer product logic, positioning, monetization, and validation.
- `references/output-standards.md`: expected artifact types and quality bars.
- `assets/knowledge-repo-readme-template.md`: reusable README scaffold for public knowledge-base repos.

## Examples

- "把林超这个领域的视频下载、转写、整理成一个长期知识库。"
- "把虎牙青年 Plus 的 B站视频按系列分类，做成 GitHub public repo。"
- "我想把某个财经 UP 主的视频变成投资研究笔记库，有没有产品化价值？"
- "把从视频到转写到总结这套流程做成可复用 Skill。"
