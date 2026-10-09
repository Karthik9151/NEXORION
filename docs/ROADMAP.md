# Roadmap and Acceptance Criteria

**Status:** Reconciled proposed roadmap. Phase numbers below are canonical for this document only; original source documents are preserved unchanged.

The source documents use different phase structures (0–5, 0–7, and 0–8) and place some work in different phases. This roadmap groups the shared intent into delivery gates without claiming any phase is complete.

## Phase 0 — Requirements and contracts

**Deliverables:** glossary and identity hierarchy; mission contract; world/evidence data concepts; autonomy tiers; threat boundaries; measurable acceptance criteria.

**Accept when:** terms are consistent; open decisions are recorded; every requirement has a verification method; simulation and lab scope are explicitly distinct.

## Phase 1 — Application foundation

**Deliverables:** minimal workspace, API skeleton, authentication/authorization approach, persistent store, migrations, structured errors, configuration and test foundation.

**Accept when:** a user can create and retrieve a mission in an authorized workspace; invalid inputs are rejected; persistence survives restart; authorization boundaries have tests.

## Phase 2 — Persistent digital world

**Deliverables:** world entities and relationships, mission linkage, state history, baseline snapshots, basic visual exploration.

**Accept when:** entities and relationships persist; changes are traceable; a baseline can be recreated and compared; the UI does not imply that modeled assets are live systems.

## Phase 3 — Deterministic end-to-end investigation

**Scenario:** investigate synthetic authentication failures.

**Deliverables:** fixed dataset/scenario, explicit hypotheses, deterministic simulation, expected outcomes, evidence capture, repeatable report.

**Accept when:** the same versioned inputs and configuration produce reproducible results; findings cite evidence; synthetic data is labelled; negative and failure cases are tested.

## Phase 4 — Independent verification and evidence integrity

**Deliverables:** evidence provenance, baseline comparison, independent verifier, discrepancy and inconclusive states.

**Accept when:** verifier can reject unsupported claims; evidence identifies its origin and run; a missing baseline or incomplete record cannot be silently treated as success.

## Phase 5 — Governance and durable coordination

**Deliverables:** machine-checkable policy checks, approval records, mission state machine, durable workflows, cancellation, retry and recovery behavior.

**Accept when:** unauthorized actions are denied at the execution boundary; approvals are scope-bound and auditable; retries do not duplicate non-idempotent actions; cancellation and restart recovery are tested.

## Phase 6 — Bounded specialist agents and adaptive interaction

**Deliverables:** typed task contracts, registry-aligned agent roles, controlled tool access, handoff reporting, adaptive interface experiments.

**Accept when:** every agent has bounded permissions and schemas; malformed outputs are rejected; model output cannot bypass policy; agent failures produce explicit blocked/incomplete states.

## Phase 7 — Isolated authorized lab

**Deliverables:** isolated environment design, egress and credential boundaries, preflight checks, approval workflow, cleanup and stop mechanisms.

**Accept when:** isolation and denial cases are tested; execution is limited to approved scope; cleanup and emergency stop are verified; audit evidence links approvals to actions. Do not begin this phase without the prior governance and verification gates.

## Phase 8 — Operational hardening and evidence-driven scale

**Deliverables:** monitoring, backup/restore, performance baselines, resource quotas, incident procedures, deployment and recovery documentation.

**Accept when:** service objectives and load targets are explicit; restore and failure recovery are tested; operational alerts are actionable; scaling components are justified by measurements.

## First vertical slice

The first complete demonstration should be a synthetic authentication-failure mission, not a real-world penetration test. It should create a mission contract, establish a baseline, run deterministic analysis, retain evidence, invoke independent verification, and generate a report with provenance and limitations.

## Cross-phase quality gates

- Security: authentication, authorization, least privilege, secret hygiene, scope enforcement, auditability.
- Reliability: schema validation, timeouts, bounded retries, cancellation, recovery, deterministic fixtures.
- Evidence: provenance, reproducibility, explicit uncertainty, verifier independence.
- AI quality: structured outputs, tool allowlists, prompt-injection resistance, no self-authorization.
- Documentation: setup and test commands verified against actual implementation; diagrams and status claims kept current.

## Status tracking

Do not mark a phase complete based on a plan or checklist alone. Completion requires artifacts and evidence that satisfy each acceptance criterion. Track planned, in progress, blocked, and verified separately.


## Stage 1 blueprint acceptance detail

Stage 1 expands blueprint finalization into a reviewable, traceable contract package. Its acceptance gate is [`stage1/07_REQUIREMENT_TO_TEST_TRACEABILITY.md`](stage1/07_REQUIREMENT_TO_TEST_TRACEABILITY.md), with overall delivery scope in [`stage1/09_STAGE1_DELIVERY_REVIEW.md`](stage1/09_STAGE1_DELIVERY_REVIEW.md).

Required deliverables:

1. Stable, prioritized requirements with dependencies and verification evidence.
2. Versioned mission/world/relationship/scenario/baseline/task/evidence/approval/verification/report contracts and a proposed `/v1` API surface.
3. Explicit mission transitions, blocked states, terminal outcomes, cancellation, bounded retries, idempotency and recovery behavior.
4. Clear autonomy tiers, workspace isolation, execution-time authorization checks, approval binding, evidence provenance, secret handling and fail-closed rules.
5. Technology decision records that distinguish proposed choices from open decisions and deferred components.
6. A deterministic synthetic authentication-failure scenario with benign and malformed negative controls, independent verification and report limitations.
7. Requirement-to-test traceability and explicit owner decisions that remain unresolved.

**Acceptance status must remain `proposed` until the project owner reviews and accepts the blueprint.** This documentation gate does not mean application code exists or that runtime/security tests have passed. Later implementation phases must produce executable tests and evidence before any functional acceptance claim.
