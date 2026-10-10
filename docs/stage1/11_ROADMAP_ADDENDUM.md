# Suggested additive section for `docs/ROADMAP.md`

Append or incorporate this section into the existing blueprint/Phase 0 section on `stag1`. Preserve the current phase structure unless the project owner explicitly approves a roadmap revision.

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
