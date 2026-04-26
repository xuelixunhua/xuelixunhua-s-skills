---
name: primitive-thinking
description: "Use when the user wants to examine an idea, tool, product, workflow, agent, SaaS direction, or tech stack through primitive, niche-opportunity, and frugal-stack thinking: 找 primitive、solution vs primitive、小众怪货、高增长 SaaS、垂直流程、AI 操作员、技术栈选择、减少依赖、降低成本、独立开发、事前规划、事后反思、runway、可被 agent 调用的能力."
---

# Primitive, Niche Opportunity, And Frugal Stack Thinking

## Mission

Help the user plan or reflect on an idea, tool, product, workflow, agent, or codebase by combining two lenses:

- **Niche opportunity lens**: what narrow, high-pain, workflow-heavy market or role action is worth productizing?
- **Primitive lens**: what reusable, composable, machine-callable capability can others build on?
- **Frugal stack lens**: what is the smallest dependable technical stack that preserves runway, ownership, and speed?

This skill is a taxonomy router. Keep `SKILL.md` lean. Use references for progressive disclosure: open only the modules needed for the user's current scope, unless they ask for full thinking.

## Success Criteria

- Classifies the user's request before analyzing it: full thinking, primitive-only, stack-only, pre-build planning, post-build reflection, or a mixed case.
- Separates market/workflow opportunity, solution-shaped surface, primitive-shaped core, and stack/infrastructure choices.
- Helps the user spot narrow but valuable vertical workflows where AI can productize repeated human operations.
- Helps the user reduce unnecessary dependencies, fixed costs, operational complexity, and enterprise-best-practice cargo culting.
- Preserves the opportunity question: where is the annoying, repeated, role-based workflow with clear ROI?
- Preserves the primitive question: what can be reused, called, composed, embedded, or built upon?
- Preserves the frugal-stack question: what constraints actually matter, and what is the simplest stack that satisfies them?
- Produces concrete next moves rather than abstract praise for simplicity.

## Trigger Surface

Use this skill when the user asks to:

- 用 primitive 思维分析一个想法、工具、产品、工作流、应用、SaaS、插件、脚本、agent、知识库或服务。
- 找某个东西里面可以 primitive 的内容，或问它能不能做成 primitive。
- 判断一个产品是 solution、primitive，还是 solution wedge + primitive core。
- 研究小众 SaaS、高增长 SaaS、垂直行业流程、AI 时代产品方向、行业 AI 操作员、非结构化数据产品化、软件加服务、轻 ERP。
- 讨论技术栈选择、减少依赖、降低成本、降低复杂度、独立开发者的最小可活技术栈。
- 对已经做出来的工具做事后复盘：哪些依赖太重，哪些服务该砍，哪些能力该沉淀为复用资产。
- 对还没开始的项目做事前规划：约束是什么，哪些技术先不上，哪些接口/数据/规则要提前稳定。
- 讨论 AI/agent 时代的产品形态：什么会被人打开，什么会被 agent 调用。

Do not trigger for ordinary debugging, generic UI design, pricing, marketing copy, or implementation help unless the user asks for opportunity selection, primitive, stack, dependency, cost, architecture, or planning/reflection analysis.

## Classification First

Before giving advice, classify the request along two axes.

**Timing axis**

- **事前规划**: the user is deciding what to build, what stack to choose, what to avoid, or how to shape the first version.
- **事后反思**: the user has already built something and wants to review stack weight, dependencies, costs, reusable cores, or next product moves.

**Lens axis**

- **Niche opportunity lens**: vertical workflow pain, role automation, human-service productization, clear ROI, small markets with urgent needs, AI-enabled product directions.
- **Primitive lens**: reusable objects, actions, data, rules, protocols, APIs, agent tools, or capability layers.
- **Frugal stack lens**: constraints, cost structure, dependency surface, deployment, storage, auth, AI usage, hosting, operations, and maintenance.
- **Full thinking**: the user asks broadly, is unsure what to inspect, or wants a complete planning/reflection pass.

## Reference Routing

Use references as progressive disclosure.

- Open `references/full-thinking-map.md` when the user asks for 全方位思考, complete planning, complete postmortem, or gives a broad idea/tool and asks what to think about.
- Open `references/niche-opportunity-lens.md` when the user focuses on product direction, high-growth SaaS patterns, 小众怪货, vertical workflows, AI operators, unstructured data productization, software-plus-service, or light industry operating systems.
- Open `references/primitive-lens.md` when the user focuses on primitive, composability, solution vs primitive, API/data/protocol/capability surfaces, or agent-callable layers.
- Open `references/frugal-stack-lens.md` when the user focuses on technology choices, cost, dependency reduction, operational simplicity, runaway cloud bills, local AI, self-hosting, or post-build stack trimming.
- If the request is mixed, open the smallest set of references that covers it. Do not load every reference by habit.

## Default Workflow

1. **Classify scope**: name the timing axis and lens axis.
2. **State the current shape**: identify the niche/workflow opportunity, the visible solution, the possible primitive core, and the current or proposed stack.
3. **Extract constraints**: customer type, painful workflow, roles involved, ROI, solo/team size, budget, traffic, reliability needs, data sensitivity, deployment skill, AI usage, expected integrations, and time horizon.
4. **Analyze with the chosen reference modules**:
   - opportunity shape if the niche opportunity lens is active
   - primitive candidates if the primitive lens is active
   - stack simplification and dependency review if the frugal stack lens is active
   - both when full thinking is active
5. **Separate keep / defer / cut / expose**:
   - keep: what is already pulling its weight
   - defer: what is plausible later but premature now
   - cut: what adds cost, dependency, or operational weight without matching current constraints
   - expose: what should become an API, schema, command, protocol, data feed, rule, or agent tool
6. **End with an experiment**: the smallest product or engineering move that tests the recommendation.

If the input is thin, make reasonable assumptions and continue. Ask only when an unknown constraint would change the recommendation materially.

## Output Guidance

Default to Chinese when the user writes in Chinese.

For full thinking, use this shape:

- **分类**: 事前/事后 + opportunity/primitive/stack/full
- **一句判断**: current overall read
- **机会层**: niche workflow, role action, ROI, and AI leverage
- **Primitive 层**: candidate reusable/callable units
- **技术栈层**: constraints, costs, dependencies, and simplification moves
- **保留 / 暂缓 / 砍掉 / 暴露**: concrete decisions
- **下一步实验**: one or more small tests

For partial requests, keep the output narrower and name which reference module guided the answer.

Avoid universal stack prescriptions. The point is not "always use Go + SQLite + VPS" or "always expose an API." The point is to choose from explicit constraints and to keep the product's reusable core visible.

## Necessary Facts And Boundaries

- Primitive means a designed, minimally meaningful, composable semantic unit that others can build on or call.
- Niche opportunity thinking means finding small-looking but high-pain vertical workflows where customers can quickly calculate saved labor, reduced errors, or increased revenue.
- Frugal stack thinking means reducing fixed cost, avoidable dependency, and operational drag while preserving enough reliability for the current constraints.
- Cost is not only money. Cost also includes cognitive load, vendor lock-in, deployment fragility, debugging surface, idle services, and future migration burden.
- A primitive can live inside a solution; a frugal stack can give that solution enough runway to discover the primitive.
- Do not shame complexity. Some constraints genuinely require managed services, queues, Postgres, Kubernetes, compliance vendors, or expensive model APIs. The skill's job is to make the constraint explicit.

## Examples

- “我刚做了一个工具，帮我用 primitive 思维看看哪些东西值得抽出来，也顺便看技术栈是不是太重。”
- “这个 idea 还没开始做，帮我做事前规划：哪些 primitive 要先想清楚，技术栈怎么选得轻一点。”
- “我这个 SaaS 已经跑起来了，帮我事后反思哪些依赖能砍，哪些能力可以做成 API 或 agent tool。”
- “我不想被企业级最佳实践绑架，帮我设计独立开发者版本的最小技术栈。”
- “我在找 AI 时代的小众 SaaS 方向，帮我判断哪些垂直流程值得做，能不能长出 primitive。”
