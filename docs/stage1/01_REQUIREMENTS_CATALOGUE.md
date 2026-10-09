# Stage 1 Requirements Catalogue

**Status:** Proposed and testable design requirements. The requirement IDs are intended to remain stable across implementation.

## Priority definitions

- **MUST / P0:** required for a trustworthy initial implementation and first vertical slice.
- **SHOULD / P1:** important for operability and should be completed before widening scope.
- **LATER / P2:** deliberately excluded from the first vertical slice; requires a later decision or evidence that it is needed.

## Product and architecture requirements

| ID | Priority | Requirement | Acceptance evidence | Dependencies |
|---|---|---|---|---|
| NXR-001 | P0 | NEXORION is the persistent modeled environment, not a specialist agent or conversational persona. | Glossary and architecture consistently distinguish world state from conversation context. | None |
| NXR-002 | P0 | NEXARCH is the proposed primary mission orchestrator and cannot grant its own authority. | Registry and coordination contract show planning separated from authorization. | NXR-005 |
| NXR-003 | P0 | ERGOUSIARCH is expressed through deterministic governance/authorization services; the name itself is not an enforcement mechanism. | Every consequential operation has an explicit policy check at the execution boundary. | NXR-005, SEC-001 |
| NXR-004 | P0 | Specialist agents have bounded responsibilities, typed inputs/outputs, and no implicit power to bypass deterministic controls. | Registry names owner, output, prohibited authority, and failure behavior for every role. | NXR-002, NXR-003 |
| NXR-005 | P0 | Planning, authorization, execution, and independent verification are separate responsibilities. | Architecture and lifecycle define separate decision points and records. | SEC-001 |
| NXR-006 | P0 | Synthetic simulation, supplied/observed evidence, and any future isolated lab execution are labeled and stored as distinct source classes. | Contract validation rejects ambiguous provenance/source class. | DAT-001, SEC-004 |
| NXR-007 | P0 | The first vertical slice is a synthetic authentication-failure investigation with deterministic expected results. | Scenario includes fixtures, baseline, expected classification, evidence, verifier checks, and pass/fail cases. | SIM-001 |

## Mission and workflow requirements

| ID | Priority | Requirement | Acceptance evidence | Dependencies |
|---|---|---|---|---|
| MIS-001 | P0 | Every mission has a durable identifier, workspace, requester, objective, scope, autonomy tier, lifecycle state, timestamps, and schema version. | Contract defines required fields and validation rules. | DAT-001 |
| MIS-002 | P0 | Mission state changes follow a finite, explicit transition table; arbitrary state edits are invalid. | Lifecycle transition tests are specified. | MIS-001 |
| MIS-003 | P0 | A mission blocked on approval or missing scope is visible as blocked and cannot start execution. | Negative tests prove no task dispatch while blocked. | SEC-001, SEC-002 |
| MIS-004 | P0 | Cancellation stops new work, signals running work, and records any work that could not be stopped immediately. | Cancellation semantics are defined and testable. | MIS-002 |
| MIS-005 | P0 | Retries are bounded, idempotent where possible, and recorded. Non-idempotent actions are not blindly replayed. | Retry policy and duplicate-submission tests are specified. | MIS-002, SEC-006 |
| MIS-006 | P0 | Every completed or failed mission has an outcome summary, limitations, and evidence/report references where available. | Terminal state invariants require a completion record. | EVD-001 |
| MIS-007 | P1 | Long-running tasks expose progress, heartbeat/lease expiry, timeout, and recovery states. | Workflow resilience tests are specified. | MIS-002 |

## Data and API requirements

| ID | Priority | Requirement | Acceptance evidence | Dependencies |
|---|---|---|---|---|
| DAT-001 | P0 | Mission, entity, relationship, scenario, baseline, task, evidence, approval, verification, and report contracts are versioned. | Contract document defines identity, required fields, source/provenance, and compatibility expectations. | None |
| DAT-002 | P0 | All data access is scoped to a workspace; client-supplied workspace IDs never override server-side authorization. | Cross-workspace negative tests are specified. | SEC-003 |
| DAT-003 | P0 | Evidence has source, producer, timestamp, integrity digest where applicable, parent/mission linkage, and collection method. | Evidence validation rejects missing provenance. | EVD-001 |
| DAT-004 | P0 | API errors use a stable machine-readable envelope and request/correlation ID. | Error contract and validation cases are defined. | API-001 |
| DAT-005 | P1 | Mutating requests that may be retried support idempotency keys or an equivalent deduplication strategy. | Replay tests distinguish same key/same payload from conflicting reuse. | MIS-005 |
| API-001 | P0 | Proposed API routes are versioned under `/v1`; request validation occurs before dispatch. | API surface and input-boundary rules are documented. | DAT-001 |
| API-002 | P1 | Live mission status updates use a defined event shape and never bypass the authenticated API authorization policy. | Event contract includes mission/workspace scope and sequence metadata. | SEC-003 |

## Security, safety, and governance requirements

| ID | Priority | Requirement | Acceptance evidence | Dependencies |
|---|---|---|---|---|
| SEC-001 | P0 | Policy is deny-by-default. Unclear scope, missing policy data, expired approval, policy service failure, or verifier failure cannot authorize execution. | Fail-closed test matrix is defined. | NXR-003 |
| SEC-002 | P0 | Approval is bound to a specific requester, workspace, target scope, action class, constraints, expiry, and a digest/version of the approved plan. | Approval mismatch and replay cases are specified. | DAT-001 |
| SEC-003 | P0 | Every read/write/query is authorized against the authenticated principal and workspace server-side. | Horizontal and vertical authorization tests are defined. | DAT-002 |
| SEC-004 | P0 | Stage 1 scenario execution is synthetic-only; no live target discovery, credential attempts, external scanning, or environment modification is permitted. | Scenario input validation and egress-denial tests are specified. | SIM-001 |
| SEC-005 | P0 | Model/agent output is untrusted data and cannot directly execute shell commands, SQL, network requests, or privileged actions. | Structured proposals must pass deterministic validation and policy gates. | NXR-005 |
| SEC-006 | P0 | Consequential actions require a separate execution-time authorization check; approval is not transferable to changed plans/scopes. | Plan-digest mismatch prevents execution. | SEC-002 |
| SEC-007 | P0 | Evidence and audit events distinguish generated hypotheses from observed/synthetic facts and preserve provenance. | Provenance label and tamper-detection tests are specified. | DAT-003 |
| SEC-008 | P0 | Secrets are server-side, never committed or exposed in client bundles/logs/reports; credentials are redacted from telemetry. | Secret scanning and redaction tests are defined for future CI. | OPS-001 |
| SEC-009 | P1 | Resource limits exist for mission time, task count, event/data size, concurrency, and retry count. | Limit-overrun tests are defined. | OPS-002 |
| SEC-010 | P1 | Audit logs record actor, action, resource, decision, reason, timestamp, correlation ID, and before/after reference where applicable. | Audit completeness tests are defined. | DAT-003 |
| SEC-011 | P1 | Future lab execution uses a separate isolated boundary and a separate later approval gate; it is not activated by this Stage 1 design package. | Deployment architecture and approval gates are documented before lab work starts. | SEC-004, open decision OD-006 |

## Simulation requirements

| ID | Priority | Requirement | Acceptance evidence | Dependencies |
|---|---|---|---|---|
| SIM-001 | P0 | The initial simulation runner evaluates only versioned synthetic fixtures with deterministic rules and without network, host-command, or real-credential capabilities. | Fixture A/B/C and egress/capability negative tests are specified. | NXR-007, SEC-004, DAT-001 |

## Evidence and verification requirements

| ID | Priority | Requirement | Acceptance evidence | Dependencies |
|---|---|---|---|---|
| EVD-001 | P0 | Evidence is append-only from the application point of view; corrections are new linked records, not silent edits. | Contract identifies immutable ID/hash and supersession links. | DAT-003 |
| EVD-002 | P0 | Origo independently checks source, scope, completeness, integrity, expected outcome, and contradictions. | Verifier contract includes `verified`, `disputed`, and `inconclusive`. | NXR-005 |
| EVD-003 | P0 | Mission success cannot be declared solely by the component that generated the result. | Success transition requires separate verification result or an explicit documented verification exception policy. | EVD-002 |
| EVD-004 | P1 | Reports disclose missing evidence, incomplete tasks, confidence limits, and synthetic-only scope. | Report template includes evidence references and limitations. | MIS-006 |

## Operations and delivery requirements

| ID | Priority | Requirement | Acceptance evidence | Dependencies |
|---|---|---|---|---|
| OPS-001 | P0 | Environment configuration, secret management, and runtime/deployment choices are documented separately from application code. | Tech decision records identify unselected operational choices. | SEC-008 |
| OPS-002 | P1 | Every asynchronous task has timeout, resource budget, retry/backoff, cancellation, and recovery semantics. | Task contract and lifecycle test matrix include each behavior. | MIS-005, MIS-007 |
| OPS-003 | P1 | Metrics and structured logs distinguish mission outcomes, policy denials, approval blocks, verifier disputes, and technical failures. | Observability event catalogue is defined. | SEC-010 |
| DOC-001 | P0 | Every P0 requirement maps to a verification method, and every open owner decision remains explicitly open until decided. | Traceability matrix has no orphan P0 requirements. | All |
| DOC-002 | P0 | Documentation never describes a proposed component or future test as implemented or passed. | Review checklist checks status wording. | All |
