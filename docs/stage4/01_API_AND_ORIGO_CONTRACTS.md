# Stage 4 — API, Origo and Report Contracts

Status: implementation contract for `stage4-implementation`; contracts are being implemented in this branch.

## Invariants

- Every authenticated workspace endpoint requires a valid session cookie and `X-Workspace-ID`; workspace membership is checked server-side.
- State-changing endpoints require the existing CSRF cookie/header pair. Session tokens are never stored in browser storage.
- The only executable scenarios are the backend's registered, inert synthetic scenarios. UI cards cannot submit arbitrary outcomes, events, code or targets.
- Simulation execution status, mission lifecycle and Origo verification status are independent dimensions. A completed simulation is not a verification.
- Origo reads persisted run/evidence records only. Missing legacy event detail is inconclusive, never silently promoted to verified.
- Each verification attempt is persisted. Idempotency keys deduplicate retries; omitting a key permits a distinct recorded attempt.
- Reports include only data associated with the authorized workspace and accurately state evidence gaps and limitations.

## API contracts

All paths below are under `/v1`.

### Scenario catalog — `GET /scenarios`

Returns registered scenarios only. Planned UI placeholders are not returned as executable scenarios.

```json
{
  "items": [{
    "id": "scenario-auth-failure-v1",
    "name": "Authentication Failure Pattern",
    "category": "IDENTITY",
    "description": "Synthetic event sequence evaluated by a fixed teaching rule.",
    "enabled": true,
    "fixture_version": "1.0.0",
    "rule_set_version": "auth-failure-rules-v1",
    "source_class": "synthetic",
    "limitations": ["Synthetic data only"]
  }],
  "catalog_version": "1.0"
}
```

### Verify a run — `POST /missions/{mission_id}/runs/{run_id}/verify`

Requires session, CSRF, workspace membership and an idempotency key when provided. Request body is empty; client-submitted evidence/outcomes are not accepted.

Returns the persisted verification record with `id`, `workspace_id`, `mission_id`, `run_id`, `status`, `verifier_version`, `schema_version`, `checks`, `reasons`, `discrepancies`, `evidence_ids`, `evidence_fingerprints`, `created_at` and `idempotency_key`.

### Verification history — `GET /missions/{mission_id}/runs/{run_id}/verification`

Returns `{ "items": [...], "latest": ... }`, ordered newest first. An empty history is valid and represented as `items: []` and `latest: null`.

### Mission report — `GET /missions/{mission_id}/report`

Returns a structured JSON report assembled from persisted mission, baseline, run, evidence and verification-history records. Includes report schema/version, scope, records, findings, verification checks, discrepancies and limitations.

### Markdown report — `GET /missions/{mission_id}/report.md`

Returns the same authorized information as `text/markdown; charset=utf-8`. This is server-generated from persisted records rather than a client-side reconstruction.

## Origo result semantics

| Status | Meaning |
| --- | --- |
| `verified` | Required integrity/provenance checks pass and persisted events independently support the claimed synthetic outcome. |
| `failed` | Required integrity or record-validation condition fails, including a digest mismatch or invalid association. |
| `disputed` | Sufficient persisted evidence contradicts a run's claimed outcome or mutually inconsistent records. |
| `inconclusive` | Evidence is missing, legacy/incomplete, or insufficient to establish an outcome. |

Checks record a stable name, pass/fail/unknown outcome, and explanation. The API returns reasons and discrepancies separately. No live environment, external telemetry or real-world security property is asserted.

## Persistence / migration

A forward-only migration adds append-only verification history with foreign keys to workspace, mission and run, a recorded list of evidence IDs and SHA-256 fingerprints, verifier/schema versions, check results, reasons, discrepancies, timestamps and a per-run idempotency uniqueness constraint. Previously applied migrations are not rewritten.

## HTTP/error behavior

- `200`: successful GET or verification response (including idempotent replay).
- `201`: newly created verification attempt.
- `400`: malformed request/idempotency key.
- `401`: missing/expired session.
- `403`: CSRF or policy failure.
- `404`: mission/run not found within the authorized workspace.
- `409`: idempotency key reused with a conflicting operation or concurrent uniqueness race not recoverable as a replay.
- Errors use the existing `{ error: { code, message, details, retryable }, request_id }` envelope. No stack traces or cross-workspace existence disclosures.

## UI event alignment

The frontend keeps the design handoff's event vocabulary (`mission.created`, `mission.opened`, `graph.node_selected`, `graph.edge_selected`, `baseline.captured`, `simulation.submitted`, `simulation.completed`, `verification.requested`, `verification.inconclusive`, `verification.disputed`, `report.generated`, `report.exported`, `session.expired`, `api.error`). These are UI events, not a claim that a live event-stream service exists. Persisted audit events are emitted separately by backend mutations.
