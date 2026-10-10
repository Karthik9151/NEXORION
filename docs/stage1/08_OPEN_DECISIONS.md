# Open Owner Decisions

These points are intentionally **not decided by the Stage 1 package**. Existing source material has differing phase structures and some conflicting role descriptions. Preserve original research documents; record the owner's decision in a later change rather than silently rewriting project history.

| ID | Decision needed | Current recommendation / default for planning | Why open / decision criteria | Blocks |
|---|---|---|---|---|
| OD-001 | Canonical authority hierarchy and reconciliation of older `Agent Identity, Responsibilities, and Coordination.md` wording with the unified architecture | Treat NEXARCH as the proposed primary orchestrator; Archon as subordinate orchestration support; preserve conflict until owner confirms | Older source describes Archon as primary coordinator; role naming affects mission control, docs and implementation | Final registry sign-off |
| OD-002 | Whether aliases remain as listed and which is canonical (`Aleph/Alpha`, `Genesis/Genarch`, `Primus/Prime/Prior`) | One role per alias group, not duplicate agent instances by name alone | Must align naming with intended conceptual model and future APIs | Final registry/schema enum sign-off |
| OD-003 | Whether synthetic tier A2 requires human approval for each run | Always enforce deterministic scope/policy; human approval default is still open | Balance friction, misuse prevention, operational ownership and risk classification | Run workflow policy configuration |
| OD-004 | Workflow runtime: Temporal vs DB-backed state machine/queue vs another engine | Keep workflow semantics engine-independent; do not deploy a broker/engine solely by name | Recovery guarantees, operating burden, cost, idempotency, developer experience | Runtime implementation |
| OD-005 | Separate agent framework or explicit typed role interfaces first | Start with typed interfaces unless an evaluated requirement justifies a framework | Frameworks do not replace authorization; evaluate capability and maintenance costs | Agent orchestration implementation |
| OD-006 | Scope, design and authorization of a future isolated lab | Not part of Stage 1; require separate design review before any lab runner | Requires concrete isolation, credential, network, kill switch, monitoring and approval model | Any lab code or provisioning |
| OD-007 | Identity/authentication and SSO strategy | No provider selected; require secure server-side identity and workspace authorization | Local-only vs OIDC/SSO, MFA, recovery, session handling, deployment audience | Account implementation |
| OD-008 | Model providers and hosted/self-hosted strategy | Provider abstraction can be considered; no provider selected | Data handling, latency, quality, cost, portability, availability, contract terms | Model integration |
| OD-009 | Deployment topology and environments | **Hard spend ceiling: $0.** Local development + existing GitHub Actions are the default; an optional hosted smoke test is allowed only on verified free tiers without attaching a payment card. No paid pilot under the current requirement. | Same-origin UI/API serving, owner bootstrap, free-tier terms/limits, data region, reliability and account provisioning remain unresolved. If no-charge conditions cannot be demonstrated, do not host. | Hosting design, production architecture and hosted smoke-test authorization |
| OD-010 | Data retention, deletion, export, encryption key ownership and residency | Evidence/audit provenance retained; exact lifecycle policy remains open | Privacy, legal requirements, user expectations and cost | Production data policy |
| OD-011 | Licence, contribution rules, support promise, versioning and vulnerability disclosure channel | Do not infer a licence or support model | These are legal/product governance choices that require explicit owner input | Public release posture |
| OD-012 | Success measures and operational objectives (latency, concurrency, availability, cost) | Define metrics for the vertical slice first; do not invent SLOs | Quantitative goals need intended users and expected load | Performance design/deployment sizing |
| OD-013 | Event transport: SSE, WebSocket, durable broker | Start with simplest transport justified by interaction requirements | Delivery/replay semantics, fan-out, throughput and operations | Live UI updates |
| OD-014 | PostgreSQL schema/migration approach and evidence blob storage | PostgreSQL as proposed metadata source of truth; blob store choice open | Artifact sizes, immutability, backup and access-control needs | Storage implementation |
| OD-015 | Exact approval roles, segregation of duties, emergency stop owner and revocation UX | No approval is authority unless validated and scoped; role catalog requires confirmation | Business ownership and deployment context vary | Policy engine and admin UX |

## How to close a decision

For each decision, record: selected option, alternatives considered, rationale, security/privacy impact, cost/operational impact, migration/reversal plan, owner and date. Update the applicable decision record and cross-reference it from the source-of-truth map. A choice is not final simply because a technology appears in a sketch or roadmap.


## OD-009 deployment record — $0 implementation policy

**Status:** Proposed deployment topology; the $0 spending ceiling is a binding owner requirement for this implementation.

- **Selected working approach:** build and test locally and with the existing GitHub Actions CI at no charge. A Render free + Neon free smoke test is optional only after their current terms and account billing controls have been checked; do not add a payment card.
- **Alternatives considered:** start with a paid host or AWS; rejected for the current project budget. Separate frontend/API hosts are not assumed safe because the session/CSRF cookie design requires a verified same-origin or explicitly engineered shared-parent-domain arrangement.
- **Rationale:** preserve a testable implementation without cloud operations overhead or billing exposure. Hosted testing must never be used to justify reliability, backup, recovery, or always-on-worker claims that free tiers cannot evidence.
- **Security and privacy:** synthetic fixtures only; secrets remain in server-side environment configuration; no live-target scanning, host commands, real credentials, or Stage 7 lab deployment. Do not put secrets in source, CI logs, client bundles, or generated reports.
- **Cost impact:** maximum planned spend is $0. Paid worker, database, model API, domain, backup, and cloud-lab costs are out of scope. If an essential acceptance gate cannot be completed for $0, mark it blocked and ask the owner to redesign scope; do not silently incur a charge.
- **Reversal plan:** if a future owner explicitly changes the budget, reassess provider, tenancy, region, backup/recovery, secret handling, and cost controls in a new decision record. Until then, skip hosted work whenever free/no-card conditions are uncertain.
- **Owner/date:** the $0 cap was specified by the project owner on 10 October 2026. Exact hosting topology and whether to run the optional hosted smoke test remain open; no deployment is authorized by this record.
