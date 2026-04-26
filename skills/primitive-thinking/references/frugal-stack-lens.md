# Frugal Stack Lens Reference

Open this reference when the user is mainly asking about technology stack selection, reducing dependencies, lowering cost, simplifying infrastructure, extending runway, or reviewing whether a built product is carrying too much operational weight.

## Core Idea

There is no universally best stack. Constraints decide the stack.

Frugal stack thinking asks: given the user's actual constraints, what is the smallest dependable system that can keep the product alive long enough to learn?

The goal is not austerity for its own sake. The goal is to protect runway, ownership, debugging clarity, and iteration speed.

## Article-Derived Anchors

- Near-zero fixed cost can create the same practical runway as a large funding buffer.
- A solo developer running multiple products may benefit more from boring, local, single-machine, low-ops choices than from enterprise cloud defaults.
- The article's example stack is not a universal recipe, but a constraint fit: solo developer, low fixed cost, multiple products, high reuse, simple deployment.
- SQLite + WAL can be enough for many products and may be faster than a network database when the app and data live together.
- A static binary or simple deployment unit can radically reduce environment and deployment burden.
- Enterprise cloud thinking can create large costs before the first real user arrives.
- Local or self-owned AI capacity can make sense for batch inference, experimentation, or repeated workloads when API bills would dominate.
- The strongest lesson is "set constraints first, choose technology second."

## Constraint Inventory

Use this list before recommending stack choices:

- Team: solo, small team, or larger team; who will operate it?
- Budget: target monthly fixed cost and acceptable variable cost.
- Runway: how long the product must survive without revenue.
- Traffic: current load, realistic near-term load, and burst patterns.
- Data: size, write concurrency, durability needs, sensitivity, backup needs.
- Reliability: acceptable downtime, recovery time, compliance, customer expectations.
- Deployment skill: what the builder can confidently debug at 2 a.m.
- Integration needs: auth, payments, email, search, storage, queues, analytics, AI.
- AI usage: interactive vs batch, model quality needs, privacy, token volume, local hardware.
- Time horizon: throwaway experiment, durable indie product, enterprise-facing product, or infrastructure primitive.

## Stack Taxonomy

### Compute And Hosting

- Frugal default: one VPS, one process or a small number of services, systemd or similarly simple process supervision.
- Consider managed/serverless when variable load, geographic latency, compliance, team familiarity, or operational constraints justify it.
- Watch for premature cloud complexity: Kubernetes, multi-AZ, service mesh, many managed services, or platform glue before real demand.

### Data

- Frugal default: SQLite + WAL for small/medium apps with low write contention and simple operational needs.
- Consider Postgres/MySQL when concurrent writes, team workflows, analytics, replication, extensions, managed backups, or ecosystem needs justify them.
- Watch for hidden costs: network round trips, managed database minimums, backup complexity, migration friction.

### Deployment

- Frugal default: simple build artifact, explicit restart command, boring logs, boring backups.
- Prefer fewer moving parts until deployment pain is real.
- Watch for "best practice" pipelines whose maintenance burden exceeds the product's maturity.

### Auth, Payments, Email, And Integrations

- Build only what is safe and small. Do not hand-roll security-sensitive complexity casually.
- Use vendors when trust, compliance, deliverability, fraud, or maintenance burden is the actual product risk.
- Watch for subscriptions that turn hypothetical future needs into immediate monthly burn.

### AI

- Use paid APIs for quality-sensitive interactive features, early validation, and cases where model operations are not core.
- Consider local models or owned hardware for repeated batch inference, prompt experimentation, privacy-sensitive processing, or large predictable volume.
- Watch for per-token tools or workflows that silently turn development into a variable cost center.

### Reuse Across Products

- Treat shared engines, libraries, schemas, prompts, deployment patterns, and internal tools as an ability asset portfolio.
- Reuse is valuable only when it reduces future build time without freezing every product into the same shape.

## Before-Build Planning

When the user is planning a new product:

1. State hard constraints first: monthly cost ceiling, operator skill, reliability needs, data shape, traffic expectation, and runway.
2. Choose a default-simple stack that can be operated by the actual builder.
3. Mark "defer until proven" items: Kubernetes, RDS, queues, distributed workers, multi-region, enterprise auth, complex observability, custom billing systems, heavy AI pipelines.
4. Identify the few interfaces that should be stable from day one: domain objects, data schema, API boundaries, event names, backup format, import/export.
5. Decide what would trigger an upgrade: write contention, downtime pain, customer requirements, data growth, compliance, team growth, or unit economics.

## Post-Build Reflection

When the user has already built something:

1. Inventory fixed monthly costs and idle services.
2. Inventory dependencies by necessity: core value, trust/compliance, convenience, habit, or fear of future scale.
3. Find operational drag: deploy pain, hard-to-debug services, fragile credentials, noisy logs, complicated local setup.
4. Ask what can be merged, self-hosted, removed, delayed, or replaced by a simpler primitive.
5. Keep managed services that carry real risk better than the builder can.
6. Convert repeated internal patterns into reusable assets only when they reduce future work.

## Red Flags

- "万一火了" is the main reason for current complexity.
- The monthly bill requires customers the product does not yet have.
- The stack has more services than the team can debug confidently.
- A managed service exists only because a tutorial used it.
- Local development is harder than production usage.
- The product cannot be backed up, restored, or redeployed simply.
- The user pays recurring cost for sporadic usage that could be batched, simplified, or deferred.

## Output Pattern

For stack analysis, capture:

- Current or proposed stack.
- Actual constraints.
- Cost and dependency map.
- What to keep, defer, cut, or simplify.
- Upgrade triggers.
- Next experiment, such as moving one service, testing SQLite + WAL, simplifying deployment, measuring real load, or replacing one vendor dependency.
