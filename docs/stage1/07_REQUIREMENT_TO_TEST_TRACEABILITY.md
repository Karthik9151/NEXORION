# Requirement-to-Test Traceability and Stage 1 Acceptance

**Status:** Test plan specification. These tests have not been run; no runtime is claimed.

## Traceability matrix

| Requirement IDs | Verification ID | Test / review | Pass condition |
|---|---|---|---|
| NXR-001, NXR-002, NXR-003, NXR-004, NXR-005 | ARCH-01 | Architecture and role-boundary review | World, orchestrator, governance and specialists are distinct; no role can self-authorize |
| NXR-006, DAT-003, SEC-007 | PROV-01 | Provenance schema review plus negative fixture test | All evidence has source class/provenance; source classes cannot be silently inferred |
| NXR-007, SIM-001, SEC-004 | SIM-01 | Run fixtures A/B/C in deterministic implementation | Expected classification for each fixture; no external I/O capability |
| MIS-001, DAT-001 | CONTRACT-01 | Contract schema validation | Required fields, enums, versions and invariants are explicit |
| MIS-002 | LIFE-01 | Transition-table test | Allowed transitions pass; all unspecified transitions fail |
| MIS-003, SEC-001, SEC-002, SEC-006 | AUTHZ-01 | Approval and fail-closed test matrix | Missing, expired, mismatched or revoked approval/policy failure blocks execution |
| MIS-004, MIS-005, MIS-007, OPS-002 | LIFE-02 | Cancellation/retry/recovery tests | Bounded and observable; no unsafe duplicate side effects; partial progress retained |
| MIS-006, EVD-002, EVD-003, EVD-004 | VERIFY-01 | Verifier/report integration test | Independent verification required; disputes/inconclusive outcomes cannot be marked successful |
| DAT-002, SEC-003 | TENANT-01 | Cross-workspace authorization test suite | No read/write/event/cancel/approval/report access across workspaces |
| DAT-004, API-001 | API-01 | Contract/error review | Versioned API shape and stable error envelope are documented |
| DAT-005 | API-02 | Idempotency replay test | Same key/same payload is deduplicated; same key/different payload is rejected |
| API-002 | API-03 | Authenticated event authorization review/test | Event subscriptions and emitted events enforce authenticated principal/workspace scope and include sequence metadata |
| SEC-005 | PROMPT-01 | Untrusted model output tests | Content cannot become arbitrary commands, policy decisions or capabilities |
| SEC-008 | SECRET-01 | Secret scanning/redaction check | No credential in committed files, client build, log examples or reports |
| OPS-001 | CONFIG-01 | Configuration and release-readiness review | Environment configuration, secret management, and runtime/deployment choices are documented without implying unresolved choices are finalized |
| SEC-009, OPS-003 | OPS-01 | Resource/error event catalogue review | Limits and unique failure/outcome telemetry are defined |
| SEC-010, EVD-001 | AUDIT-01 | Audit/evidence mutation test | Required actions recorded; correction uses supersession, not silent edit |
| SEC-011 | LAB-01 | Architecture boundary review | Future lab is clearly separate and unavailable in Stage 1 |
| DOC-001, DOC-002 | DOC-01 | Documentation review | Every P0 requirement has verification; no unapproved owner decision is represented as final |

## Stage 1 documentation acceptance gate

Stage 1 is ready for owner review when:

- [ ] Source-of-truth document acknowledges the Stage 1 package and links it without deleting earlier research.
- [ ] NEXORION, NEXARCH and ERGOUSIARCH definitions are consistent or differences are recorded as open decisions.
- [ ] Every specialist role has clear responsibilities and prohibited authority; aliases do not become duplicate authorities.
- [ ] P0 requirements have IDs, dependencies and verification methods.
- [ ] Mission, world entity, relationship, scenario, baseline, task, evidence, approval, verification and report contracts are defined.
- [ ] Mission states/transitions, terminal behavior, cancellation, retry/deduplication and recovery semantics are explicit.
- [ ] Autonomy tiers and synthetic/observed/future-lab source classes are distinct.
- [ ] Policy and approval behavior is fail-closed and checked at the execution boundary.
- [ ] Tenant isolation, untrusted model output, secret handling, audit and evidence provenance requirements are explicit.
- [ ] First vertical slice has deterministic fixtures, expected outcomes, negative cases and report limitations.
- [ ] Technology status distinguishes proposal, selected direction, open decision and deferred component.
- [ ] Owner decisions remain visible; there is no implicit final choice for identity, model provider, deployment, retention, licence or human approval policy.
- [ ] All materials state that tests are specified, not yet executed, and features are not implemented.

## Future implementation release gate (not Stage 1 completion)

Before declaring a working first vertical slice, the implementation must pass executable tests for lifecycle, scope and authorization, fixture determinism, provenance, independent verification, cancellation/recovery, tenant isolation, API error behavior and secret scanning. A document checklist alone is not evidence that those tests passed.

## Suggested CI test labels for later phases

`contracts`, `mission-state-machine`, `approval-policy`, `workspace-isolation`, `evidence-provenance`, `synthetic-scenario`, `independent-verification`, `cancellation-recovery`, `secret-scan`, `dependency-audit`, `api-errors`.
