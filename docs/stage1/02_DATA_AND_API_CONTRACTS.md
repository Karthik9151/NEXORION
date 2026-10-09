# Data and API Contracts — Stage 1

**Status:** Conceptual contracts for implementation planning. These are not deployed schemas or a published OpenAPI document.

## Contract-wide rules

1. Every persisted object has an immutable UUID `id`, `schema_version`, server-generated timestamps and `workspace_id` when tenant-scoped.
2. Use UTC RFC 3339 timestamps and explicit enumerations rather than free-text state values.
3. Validate input at the API boundary and again at the privileged execution boundary.
4. Derive workspace identity from the authenticated server-side principal; a body field cannot grant access.
5. Evidence source classes are `synthetic`, `user_supplied`, `observed`, and `future_lab`. Stage 1's vertical slice permits only synthetic fixtures.
6. Unknown fields must not change authorization semantics. Reject them at security-sensitive boundaries unless a documented compatibility rule applies.
7. Approval and plan digests must use canonical serialization and a documented hash algorithm, not arbitrary JSON text.

## Common fields

```json
{
  "id": "uuid",
  "schema_version": "1.0",
  "workspace_id": "uuid",
  "created_at": "server-generated RFC3339 timestamp",
  "created_by": "principal-id"
}
```

## Core contracts

### Mission

Required fields: `id`, `schema_version`, `workspace_id`, `requester_id`, `objective`, `scope`, `autonomy_tier`, `state`, `created_at`, `updated_at`. Optional linked references: `plan_digest`, `approval_ids`, `task_ids`, `evidence_ids`, `verification_id`, `report_id`.

Example:

```json
{
  "id": "mission-uuid",
  "schema_version": "1.0",
  "workspace_id": "workspace-uuid",
  "requester_id": "principal-uuid",
  "objective": "Evaluate synthetic authentication failure events",
  "scope": {
    "mode": "synthetic_only",
    "scenario_ids": ["scenario-auth-failure-v1"],
    "entity_ids": ["entity-lab-user-001"],
    "excluded_targets": ["all external systems"]
  },
  "autonomy_tier": "simulate_synthetic",
  "state": "draft",
  "plan_digest": null,
  "approval_ids": [],
  "task_ids": [],
  "evidence_ids": [],
  "verification_id": null,
  "report_id": null,
  "schema_version": "1.0"
}
```

Invariants: state changes only through the lifecycle service; synthetic missions cannot dispatch network/host-execution capabilities; the effective plan is canonicalized and policy-checked before dispatch; terminal mission records are immutable. A rerun creates a new mission or linked run record.

### World entity and relationship

An entity has `entity_type`, `name`, `environment_id`, `source_class`, validated `attributes`, labels and optional validity interval. Do not store secrets or executable directives in `attributes`.

A relationship has `from_entity_id`, `relationship_type`, `to_entity_id`, `source_class`, evidence references and validity interval. Both endpoints must belong to the authorized workspace or a versioned shared fixture catalog. Cross-workspace edges are invalid.

### Scenario and baseline

A scenario defines deterministic fixture inputs, fixture version, rule-set version, expected outcome, constraints and source class. A baseline captures the initial synthetic state with schema version, scenario reference, state digest, capture time and assumptions.

Example scenario:

```json
{
  "id": "scenario-auth-failure-v1",
  "schema_version": "1.0",
  "source_class": "synthetic",
  "fixture_version": "1.0.0",
  "rule_set_version": "auth-failure-rules-v1",
  "inputs_ref": "fixture://auth-failure/sequence-a",
  "expected_outcome": "suspicious_auth_pattern",
  "constraints": {
    "external_network": false,
    "real_credentials": false,
    "host_execution": false
  }
}
```

### Task

Required fields: `workspace_id`, `mission_id`, bounded role/task type, input references, declared capability set, state, attempt count, `max_attempts`, timeout, result evidence references and idempotency key. Capability declarations are ceilings, not permissions; runtime authorization checks the task, mission, approval and policy together.

### Evidence

Required fields: identity/version, workspace and mission references, optional task reference, evidence type, source class/reference, producer/version, capture time, content digest, parent references and limitations. Corrections create linked records (for example, `supersedes_evidence_id`); silent in-place changes are prohibited. A digest provides integrity checking only when canonicalization and storage protections are defined; it does not prove the source is truthful.

### Approval

Record the requester and approver, decision, action class, scope and plan digests, constraints, reason, creation/expiry times and consumption/revocation state. For consequential actions, requester/approver separation is required. Approval is narrow, expires, is replay-protected and must be checked again at execution time. Whether every synthetic run needs a human approval remains an owner decision; deterministic policy validation is mandatory either way.

### Verification

Record mission/workspace, independent verifier role, status, checks, evidence references, contradictions, limitations and verification time. Status values: `verified`, `disputed`, `inconclusive`. Missing required evidence or a failed mandatory check prevents `verified`.

### Report

Record mission/workspace, outcome, summary, classification/rule-set version, linked evidence, verification reference, limitations and generated time. State clearly when the result applies only to a synthetic fixture rather than a real system.

## Standard API error envelope

```json
{
  "error": {
    "code": "SCOPE_NOT_AUTHORIZED",
    "message": "The requested resource is not available in this workspace.",
    "details": [],
    "retryable": false
  },
  "request_id": "opaque-correlation-id"
}
```

Do not disclose stack traces, secrets, cross-workspace existence clues or sensitive policy internals in public errors. Protected audit records may hold detailed reasons.

## Proposed API surface — not implemented

| Method | Route | Purpose | Boundary |
|---|---|---|---|
| POST | `/v1/missions` | Create draft | Authenticate; derive workspace; validate scope |
| GET | `/v1/missions/{mission_id}` | Read mission | Workspace authorization |
| POST | `/v1/missions/{mission_id}/validate` | Validate objective/scope | No execution side effects |
| POST | `/v1/missions/{mission_id}/plan` | Produce versioned plan | Planning grants no authority |
| POST | `/v1/missions/{mission_id}/approve` | Request/record decision | Reviewer separation and digest binding |
| POST | `/v1/missions/{mission_id}/run` | Request synthetic execution | Re-check policy, approval and plan digest |
| POST | `/v1/missions/{mission_id}/cancel` | Cancel mission | Authorized, idempotent cancellation |
| GET | `/v1/missions/{mission_id}/events` | Progress/events | Workspace authorization and bounded pagination |
| GET | `/v1/missions/{mission_id}/evidence` | Evidence metadata | Authorization and redaction |
| GET | `/v1/missions/{mission_id}/report` | Report | Authorization and explicit limitations |
| GET | `/v1/world/entities` | Query world model | Workspace filtering and bounded result size |
| GET | `/v1/health` | Process health | No secret/infrastructure leakage |
| GET | `/v1/ready` | Dependency readiness | Safe operational diagnostics |

Endpoint names, authentication protocol, pagination convention and streaming transport require an owner decision before implementation. Listing a route here does not mean it exists.
