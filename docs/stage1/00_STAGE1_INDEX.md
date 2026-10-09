# Stage 1 Blueprint Index

**Branch:** `stag1`  
**Status:** Documentation-only planning package; owner review required.

Stage 1 turns the NEXORION concept into a coherent, testable blueprint. It does not implement executable software.

## Deliverables

1. [Requirements catalogue](01_REQUIREMENTS_CATALOGUE.md) — priorities, stable IDs, dependencies, acceptance evidence.
2. [Data and API contracts](02_DATA_AND_API_CONTRACTS.md) — proposed versioned object contracts and /v1 route surface.
3. [Mission lifecycle](03_MISSION_LIFECYCLE.md) — state machine, transitions, retries, cancellation and recovery.
4. [Governance and security controls](04_GOVERNANCE_SECURITY_CONTROLS.md) — autonomy, authorization, workspace isolation and fail-closed rules.
5. [Technology decision records](05_TECHNOLOGY_DECISION_RECORDS.md) — proposed directions, deferred technologies and explicit unresolved choices.
6. [Synthetic authentication-failure scenario](06_SYNTHETIC_AUTH_FAILURE_SCENARIO.md) — deterministic fixtures, expected outcomes and verifier checks.
7. [Requirement-to-test traceability](07_REQUIREMENT_TO_TEST_TRACEABILITY.md) — links requirements to verification and acceptance criteria.
8. [Open decisions](08_OPEN_DECISIONS.md) — choices reserved for explicit owner input.
9. [Delivery review](09_STAGE1_DELIVERY_REVIEW.md) — scope, non-goals and claims the documentation does or does not support.

Addenda for the repository's source-of-truth and roadmap documents are in [10_SOURCE_OF_TRUTH_ADDENDUM.md](10_SOURCE_OF_TRUTH_ADDENDUM.md) and [11_ROADMAP_ADDENDUM.md](11_ROADMAP_ADDENDUM.md).

## Canonical identity baseline proposed for review

- **NEXORION:** persistent digital environment and world model.
- **NEXARCH:** primary mission reasoning and orchestration layer; it cannot authorize its own consequential actions.
- **ERGOUSIARCH:** governance concept implemented through deterministic policy, approval, audit and execution-gate controls; the name itself is not an enforcement mechanism.
- **Archon:** orchestration support under NEXARCH, not a competing primary orchestrator.
- **Origo:** independent verification role, separate from result generation.

Agent aliases documented in the source material refer to roles, not duplicate agents. Conflicts in the originals are not silently erased; unresolved ownership choices are listed in the decision log.

## Safety boundary

The first vertical slice uses synthetic authentication-failure data only. No live target discovery, credential attempts, external scanning, shell execution against targets, or real-world modification is in scope. Any future isolated lab requires a separate design and approval gate.

## Acceptance

Use [requirement-to-test traceability](07_REQUIREMENT_TO_TEST_TRACEABILITY.md) and the [delivery review](09_STAGE1_DELIVERY_REVIEW.md). A requirement being specified is not evidence that it is implemented or tested. No application source, deployment or merge is part of this documentation-only scope.
