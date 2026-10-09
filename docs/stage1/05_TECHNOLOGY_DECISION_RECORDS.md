# Technology Decision Records — Stage 1

**Status:** Decision register for architecture planning. Proposed technologies are not installed, verified, or binding until accepted and implemented.

## ADR-001 — Interactive workspace

**Proposed direction:** React + TypeScript + Vite. React Flow is a candidate for editing/visualizing the entity and dependency graph.

**Rationale:** Broad ecosystem, component architecture, type support, and a fast local development loop.

**Alternatives:** Vue/Svelte or a server-rendered UI; hand-built SVG/canvas versus React Flow.

**Risks and checks:** Accessibility, large graph performance, keyboard navigation, version compatibility and avoiding visualization becoming the source of truth. The backend remains authoritative for world state and permissions.

**Status:** Proposed. Confirm UI workflows and usability requirements before locking dependencies.

## ADR-002 — API and data validation

**Proposed direction:** Python + FastAPI + Pydantic for a typed service boundary and validation.

**Rationale:** Clear request/response contracts, Python interoperability for data and simulation work, and schema-oriented validation.

**Alternatives:** Django/DRF, Flask, or a TypeScript backend. Choose based on team expertise, auth requirements, operations and integration constraints.

**Status:** Proposed; API shape in Stage 1 is a planning contract, not an OpenAPI or running service.

## ADR-003 — Persistent relational data

**Proposed direction:** PostgreSQL as authoritative metadata store for workspaces, missions, entities, relationships, approvals, tasks, evidence metadata, verification and reports.

**Rationale:** Transactions, constraints, migration tooling, access control patterns and operational maturity.

**Alternatives:** SQLite for local single-user experiments; other relational stores if deployment constraints justify them.

**Risks and checks:** Tenant isolation, migration discipline, transaction boundaries, audit immutability, backups, data deletion/retention, encryption and expected load. Evidence blobs may need a separate object store; selection is open.

**Status:** Proposed; no schema or database instance is claimed to exist.

## ADR-004 — Initial graph and digital-world model

**Proposed direction:** Represent world entities and relationships in PostgreSQL first; use NetworkX in-process for local deterministic graph analysis if needed.

**Rationale:** Avoid introducing another database before query, traversal and scale requirements are measured.

**Alternatives:** A dedicated graph database, graph extensions, or client-side-only graph state.

**Decision trigger:** Benchmark representative traversal/query needs, data volume, update frequency, concurrency and consistency. React Flow is only a view/editor; it is not the authoritative graph store.

**Status:** Proposed and intentionally conservative.

## ADR-005 — Mission workflow durability

**Candidates:** (a) a PostgreSQL-backed explicit state machine/worker queue initially; (b) Temporal when durable long-running workflows, retries, signals, timers and recovery complexity justify its operational model; (c) another workflow engine after evaluated comparison.

**Recommendation:** Keep lifecycle semantics engine-independent. Do not choose Temporal solely because it appears in concept material, and do not mistake an application agent framework for a durable workflow engine.

**Decision criteria:** Crash recovery, event history, idempotency, cancellation semantics, human approval waits, operational cost, self-hosting complexity, developer experience and deployment skills.

**Status:** Open. ADR must be revisited after one vertical slice's recovery needs are understood.

## ADR-006 — Agent role implementation

**Proposed direction:** Begin with explicit typed interfaces and deterministic service modules for each bounded responsibility. A role may initially be ordinary code rather than a separate autonomous LLM process.

**Alternatives:** Agent frameworks or multi-agent orchestration libraries.

**Rationale:** Typed inputs/outputs, clear execution boundaries and independently testable policy checks are more important than framework branding.

**Decision criteria:** Actual need for tool routing, message/state management, model heterogeneity, observability, retry semantics and maintenance overhead. A framework does not replace authorization, scope checks or audit.

**Status:** Open; no framework selected.

## ADR-007 — Live mission events

**Candidates:** Server-Sent Events for one-way progress; WebSockets for bidirectional low-latency interaction; durable broker only when throughput/replay/fan-out requirements justify it.

**Recommendation:** Begin with the simplest authenticated transport that satisfies validated interaction requirements.

**Security requirements:** Every connection and event is authorized to principal/workspace/mission; sequence IDs and bounded payloads are defined; reconnect cannot leak another workspace's events.

**Status:** Open.

## ADR-008 — Model providers and inference

**Direction:** No model provider or hosted/self-hosted deployment selected. Keep model invocation behind an explicit service boundary if introduced.

**Evaluation criteria:** Data retention and training policy, residency, latency, quality, cost, rate limits, availability, portability, structured output behavior and incident response.

**Security requirements:** Model output stays untrusted; avoid sending secrets or unnecessary personal data; redact sensitive telemetry; do not grant providers access to tools or data merely by inclusion in prompts.

**Status:** Open owner decision.

## ADR-009 — Deployment, identity and secrets

Local development is the initial working assumption, not a production deployment decision. Production topology, hosting, SSO/OIDC, MFA, session policy, secret manager, CI/CD, backup/restore, encryption key ownership and operational monitoring remain open.

Any future implementation must keep credentials server-side, separate development/test/production environments, define secret rotation and revocation, and avoid exposing internal infrastructure details through health endpoints.

**Status:** Open; no deployment or provider integration is included in Stage 1.

## ADR-010 — Tests, telemetry and quality gates

**Proposed direction:** Automated unit and contract tests, deterministic fixture tests, cross-workspace authorization negative tests, and integration tests for mission lifecycle and verifier behavior. Add dependency/security checks and secret scanning when source code and CI are introduced.

**Observability direction:** Structured events with request/correlation ID, mission ID, task ID, policy decision, state transition and verifier result; redact credentials and sensitive content.

**Status:** Required design direction. Exact test runner, CI platform, logs/metrics backend and service objectives are not yet selected.

## Deferred technologies and explicit non-decisions

- Kafka/Redpanda: do not introduce a durable streaming broker before throughput, replay or fan-out needs are measured.
- Dedicated graph database: defer until relational representation and in-process graph analysis are shown inadequate.
- Three.js/advanced 3D: future UI option after specific interaction value is established.
- Full autonomous agent framework: defer until a requirement cannot be met safely by typed role interfaces and deterministic modules.
- Isolated lab and real-world actions: outside Stage 1; require a separate threat model, isolation design and approval decision.

## Change record expectation

Each final technology choice should record owner, date, selected option, alternatives, rationale, security/privacy and cost impacts, migration/reversal path, and the evidence that triggered the decision. Appearance in a concept document is not a final selection.
