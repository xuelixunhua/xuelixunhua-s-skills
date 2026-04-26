# Full Thinking Map

Open this reference when the user asks for a complete planning or reflection pass, or when the request is broad enough that niche opportunity, primitive thinking, and frugal stack thinking all matter.

## High-Level Frame

A durable independent product needs three kinds of discipline:

- **Opportunity discipline**: do not start from hot technology or large abstract markets; find a narrow, painful, repeated workflow with clear ROI.
- **Primitive discipline**: do not only build a packaged workflow; discover the reusable capability, object model, rule, data layer, protocol, or agent-callable unit inside it.
- **Stack discipline**: do not let enterprise defaults, fashionable tools, or hypothetical scale consume runway before the product has earned them.

The three lenses reinforce each other. A niche workflow gives the product a wedge. A primitive core gives it leverage beyond a single UI. A frugal stack gives it enough time to discover both.

## Classification Taxonomy

| Timing | Opportunity Questions | Primitive Questions | Stack Questions | Typical Output |
| --- | --- | --- | --- |
| 事前规划 | Which narrow workflow, role action, or painful coordination loop is worth productizing? | What reusable unit should stay visible from day one? What domain objects/actions/rules might become stable contracts? | What constraints decide the stack? What should be deferred until proven? | A narrow first version, explicit non-goals, upgrade triggers, stable core contracts |
| 事后反思 | Is the product embedded in a high-pain workflow with clear ROI, or just a nice tool? | What repeated internal pieces are trying to become primitives? What should be exposed, packaged, or split from workflow glue? | What costs, vendors, services, and operational burdens are not pulling their weight? | Keep/defer/cut/expose decisions, simplification plan, primitive experiments |

## Full Planning Pass

Use this when the user has an idea or is about to build.

1. **Define the bet**
   - Who is the first user or caller?
   - What painful job does the first version solve?
   - Is the initial wedge a human-facing solution, a developer-facing primitive, or both?
   - Is this a narrow workflow with enough pain, frequency, and ROI?

2. **Set constraints**
   - Team size, monthly cost ceiling, runway target, deployment skill, reliability need, data shape, and AI usage.
   - Name the default: experiment, indie product, B2B tool, agent tool, infrastructure primitive, or enterprise-facing system.

3. **Identify primitive candidates**
   - Objects: durable nouns.
   - Actions: repeatable verbs.
   - Data: normalized, trusted, queryable sources.
   - Rules: scoring, validation, permissions, compliance, evaluation.
   - Protocols: schemas, commands, events, handshakes.
   - Capabilities: callable execution that others do not want to rebuild.

4. **Choose the smallest dependable stack**
   - Pick the least complex compute, data, deployment, auth, AI, and integration choices that satisfy actual constraints.
   - Mark what is intentionally not being used.
   - Define upgrade triggers before paying for future scale.

5. **Design the first contract**
   - Even if the first product is UI-first, decide what data schema, API, command, export format, or agent tool contract should remain stable.

6. **Plan experiments**
   - Product experiment: prove someone wants the job solved.
   - Opportunity experiment: prove the workflow is frequent, painful, role-based, and budget-connected.
   - Primitive experiment: prove another workflow, user, or agent wants to call the capability.
   - Stack experiment: prove the cheap/simple path handles real load and real operations.

## Full Reflection Pass

Use this when the user already built a tool, SaaS, agent, script, or internal system.

1. **Map the current artifact**
   - Visible solution surface.
   - Niche workflow or market wedge.
   - Existing stack and vendors.
   - Recurring internal objects/actions/data/rules.
   - Current monthly fixed cost and operational pain.

2. **Separate value from packaging**
   - What narrow workflow pain does this actually remove?
   - Can the buyer quickly calculate saved labor, fewer errors, or more revenue?
   - What do users open?
   - What do systems or agents call?
   - What would still be valuable if the UI were replaced?
   - What depends on taste, service, or bespoke workflow?

3. **Find primitive cores**
   - Repeated logic.
   - Stable data model.
   - Useful API boundary.
   - Internal tool that another product could call.
   - Rule/evaluation/scoring system.
   - Dataset or index that becomes more valuable with use.

4. **Audit stack weight**
   - Fixed costs.
   - Idle services.
   - Vendor lock-in.
   - Deployment fragility.
   - Debugging burden.
   - Data backup and restore clarity.
   - AI token or inference cost.

5. **Classify decisions**
   - **Keep**: earns its complexity through reliability, trust, revenue, or speed.
   - **Defer**: plausible later, premature now.
   - **Cut**: current cost or complexity without matching constraint.
   - **Expose**: should become a contract, API, schema, data feed, command, or agent tool.
   - **Consolidate**: repeated assets that should be shared across products.
   - **Narrow**: the product is too horizontal; choose a more specific workflow, role, or industry.

6. **Define the next smallest move**
   - Remove one dependency.
   - Move one service to a simpler deployment.
   - Draft one primitive contract.
   - Publish one internal capability as an agent tool.
   - Measure real load before upgrading.
   - Write backup/restore before adding infrastructure.

## Questions To Ask The User Only If Needed

Ask at most one or two when the answer would change the recommendation:

- What is your monthly fixed cost ceiling?
- Are you solo, or will someone else operate this?
- What is the most expensive or annoying dependency today?
- Is the product mainly opened by humans, called by systems, or both?
- What must not break: money, data, trust, compliance, latency, or convenience?

## Compact Output Template

```markdown
**分类**
事前/事后 + primitive/stack/full

**一句判断**
...

**机会层**
- Workflow:
- Buyer/role:
- ROI:
- AI leverage:

**Primitive 层**
1. Candidate: ...
   Caller:
   Contract:
   Composition:
   Risk:

**技术栈层**
- Constraints:
- Keep:
- Defer:
- Cut:
- Upgrade triggers:

**下一步实验**
...
```
