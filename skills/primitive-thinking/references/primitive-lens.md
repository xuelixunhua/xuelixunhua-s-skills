# Primitive Lens Reference

Open this reference when the user is mainly asking about primitive, composability, solution vs primitive, reusable capability layers, APIs, protocols, data objects, or agent-callable surfaces. If the user also asks about stack cost, dependency reduction, or pre/post planning, combine it with `frugal-stack-lens.md` or `full-thinking-map.md`.

## Core Definition

In product and startup thinking, a primitive is not merely a low-level programming type. It is a designed, minimally meaningful unit that other builders, systems, or agents can use as material.

Short form: primitive is the thing used to make other things.

## Primitive Versus Solution

| Dimension | Solution-shaped | Primitive-shaped |
| --- | --- | --- |
| Primary buyer or user | A human completing a workflow | A developer, system, team, or agent building another workflow |
| Value center | Interface, flow, convenience, packaged outcome | API, object, data, rule, protocol, permission, capability |
| Composition | Mostly self-contained | Designed to combine with other pieces |
| AI pressure | Easier for AI to recreate or customize | More likely to be called by AI and agents |
| Durable question | Will people keep opening this? | Will other systems keep calling this? |

## Before And After Use

**事前规划**

- Decide which domain nouns and verbs should become stable early.
- Keep the first solution narrow, but avoid burying the reusable core inside UI-only workflow glue.
- Choose contracts that can survive UI changes: schema, API, command, event, rule, data feed, or agent tool.
- Defer primitives that do not yet have repeated callers.

**事后反思**

- Look for repeated internal operations, copied logic, recurring data models, integrations, or manual procedures.
- Ask which pieces would still matter if the UI were replaced by an agent-generated interface.
- Split durable objects/actions/rules from bespoke workflow glue.
- Test primitive demand before turning every internal helper into a public platform.

## Article-Derived Anchors

- Software does not disappear; solution-shaped software gets commoditized faster.
- The valuable layer moves behind the interface, toward callable capabilities.
- AWS chose primitives such as virtual machines, object storage, and queues instead of one packaged hosting solution.
- Stripe is primitive-shaped because payment concepts become stable objects such as customers, payment methods, accounts, charges, and payment intents.
- Primitive thinking is not about company size. Small teams can build primitives if they start from composable capability instead of a complete app surface.
- In AI-era product thinking, the future customer may be an agent. Humans buy solutions; agents call primitives.

## Candidate Primitive Types

- Object primitive: customer, payment method, document, task, identity, asset, claim, source, entity.
- Action primitive: send, verify, charge, classify, extract, rank, reconcile, deploy, monitor.
- Data primitive: canonical dataset, index, normalized feed, enriched profile, event stream, ground-truth table.
- Rule primitive: policy engine, permission model, validation rule, compliance check, scoring rubric.
- Protocol primitive: schema, message format, command contract, integration spec, workflow handshake.
- Capability primitive: reliable execution of a scarce action, such as email delivery, browser automation, OCR, fraud detection, search, retrieval, or deployment.
- Agent primitive: tool schema, callable action, memory operation, evaluation harness, planner/executor boundary, observable environment action.

## False Positives

- A feature list is not a primitive unless the features share a stable composable contract.
- A UI component is not automatically a primitive. Ask whether the value survives when the UI is replaced.
- A one-off automation is usually not a primitive until it has a reusable contract, variable inputs, and repeated callers.
- A platform is not necessarily primitive. Some platforms are just large packaged solutions.
- Raw data is not automatically primitive. It becomes primitive when it is normalized, trusted, documented, queryable, and useful across workflows.
- An API wrapper is not enough. The wrapper must add semantic clarity, reliability, trust, data, permissions, or composition value.

## Useful Discussion Prompts

- What part of this tool would still be valuable if every user could generate their own UI?
- Which internal nouns and verbs recur across use cases?
- What would an agent call here if it never opened the app?
- What object model would make this domain easier to build in?
- Which piece could become a stable contract that many workflows depend on?
- What currently feels like workflow glue but could become a reusable capability?
- Which part creates leverage as usage grows?
- What would developers or other products build if this existed as an API, data feed, protocol, or tool contract?

## Output Pattern

For each candidate primitive, capture:

- Name: short, domain-specific name.
- Caller: who or what repeatedly uses it.
- Contract: API, schema, command, protocol, data feed, rule, or tool interface.
- Compositions: 2-3 examples of what can be built with it.
- Leverage: why repeated calls increase value.
- Risks: why it may remain a solution or one-off feature.
- Next experiment: smallest way to test real caller demand.

## Trigger Evaluation Prompts

These should activate the skill:

- “我做了一个 Chrome 插件，帮我找里面可 primitive 的东西。”
- “这个工作流产品会不会被 AI 打掉？怎么转成 primitive？”
- “我有个数据清洗工具，能不能变成 agent 会调用的能力？”
- “帮我把这个 idea 拆成 solution 层和 primitive 层。”

These should not activate by default:

- “帮我写一个产品介绍。”
- “这个工具怎么定价？”
- “帮我设计首页。”
- “帮我修这个 API 报错。”
