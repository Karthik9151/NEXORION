# NEXORION Stage 5 — Implementation Status and Evidence

**Branch:** `stage5-implementation`  
**Validated base:** `main` at `30bb0464e76e53979b7b7650e9e12b3b5161820e`  
**Budget:** $0; no deployment or paid resources  
**Status:** In progress — acceptance not established

This record distinguishes code present from behavior demonstrated. It is not a Stage 5 completion certificate.

## Requirement-to-file-to-test map

| Requirement slice | Implementation locations | Verification/evidence status |
|---|---|---|
| Canonical 19-state lifecycle and allowed transitions | `backend/app/services/lifecycle.py`; `backend/app/routes/lifecycle.py`; `backend/app/models.py` | Initial transition-matrix tests in `backend/tests/test_stage5_lifecycle.py`; execution/CI result must be checked on this branch head |
| Version checks and terminal metadata | `backend/app/services/lifecycle.py`; migration `backend/alembic/versions/0004_stage5_governance_jobs.py` | SQLite/PostgreSQL migration CI is configured; actual branch-head result not yet recorded here |
| Scoped approvals and revocation | `backend/app/routes/approvals.py`; `backend/app/stage5_models.py`; lifecycle queue gate | Provisional safe default: distinct workspace owner, no self-approval, each synthetic run needs approval. OD-003 and OD-015 remain open; this is not final organizational policy |
| Durable job records/idempotency | `backend/app/routes/jobs.py`; `backend/app/stage5_models.py`; migration 0004 | Unique idempotency constraint and one-active-job check implemented; duplicate-request concurrency needs CI verification |
| Lease claim, heartbeat, uncertain recovery and stop acknowledgement | `backend/app/services/job_leases.py` | PostgreSQL `SKIP LOCKED` claim path and fail-closed lease expiry logic exist. No continuously running worker loop or periodic recovery scheduler is wired into application startup yet |
| Synthetic execution boundary and Origo separation | `backend/app/routes/simulation.py`; `backend/app/routes/research.py` | Direct draft execution is blocked; execution requires a queued, approved job. Simulation completion enters `verifying`; only Origo can establish the terminal verdict |
| Workspace authorization | lifecycle, approval, and job routes use server-side membership and workspace-scoped lookups | Existing authorization suite plus Stage 5 tests require fresh branch-head verification |
| PostgreSQL concurrency | `backend/tests/test_stage5_postgres.py`; `.github/workflows/backend-ci.yml` | CI configured for PostgreSQL 16 and a dedicated API test database; results are not claimed until the run is inspected |
| Frontend lifecycle integration | `frontend/src/api.ts`; `frontend/src/App.tsx`; `frontend/e2e/stage4.spec.ts` | UI now sends server lifecycle commands and displays the approval gate via API error feedback. Full visual and E2E regression remains to be confirmed |

## Migration and compatibility

Migration `0004_stage5_governance_jobs` follows `0003_origo_verification`. It adds nullable `missions.terminal_at` and `missions.completion_reason`, and creates:

- `mission_transition_events`
- `mission_approvals`
- `mission_jobs`
- `mission_job_attempts`

The migration does not rewrite earlier migrations or synthesize terminal timestamps for historical rows. Downgrade drops the new Stage 5 tables and terminal metadata columns; it does not delete prior Stage 2–4 records. Verify upgrade, downgrade to `0001_initial`, and re-upgrade on SQLite and PostgreSQL 16 before acceptance.

## Security behavior intended by this branch

- Client requests specify commands, not arbitrary target states.
- Compare-and-swap checks use the mission version and current state.
- Terminal records are not reopened through normal workflow commands.
- Approval must be current, unconsumed, scoped to the mission, bound to a canonical execution-contract digest/version, and unrevoked.
- Queueing accepts only a registered scenario included in the synthetic-only mission scope.
- The durable job lease is committed before deterministic work begins.
- Lease expiry produces an uncertain/review-required outcome; it never authorizes automatic replay.
- Simulation completion remains separate from the persisted Origo verification verdict.
- Job/approval/lifecycle records use existing audit events plus append-only lifecycle transition records. No credentials or session tokens are intentionally recorded.

## Known limitations / not yet accepted

1. **Worker lifecycle:** the current synthetic execution is performed synchronously in the authenticated API request after a durable claim. There is not yet a continuously running bounded worker loop or periodic startup/recovery reconciler. The lease service functions exist, but automatic recovery behavior is not fully wired.
2. **Cancellation signaling:** API cancellation is durable and idempotent, and a worker stop-acknowledgement service exists. A separate long-running worker/heartbeat loop is not wired, so active cancellation and actual process termination are not yet demonstrated end-to-end.
3. **Retries:** no automatic retry is performed. This is intentionally safer than replaying an unknown outcome, but the requested classified transient retry policy is not complete.
4. **Approval UX and owner policy:** OD-003 (A2 per-run human approval) and OD-015 (approval roles, separation of duties, emergency-stop ownership, revocation UX) remain owner decisions. The implemented distinct-owner approval is a provisional safe default, not a finalized organization policy. Single-owner workspaces will block execution.
5. **Plan model:** the digest currently binds the persisted mission objective, scope, and autonomy tier; a distinct immutable typed-plan entity is not yet implemented. Do not describe this as full plan-version governance.
6. **Audit completeness:** transition history has old/new state, actor/service, timestamp, reason, request ID, and object version. Full audit metadata parity for all approval, lease, cancellation, and recovery events still requires review.
7. **Tests:** local execution was not available in the implementation environment. No tests are marked passed in this report until the GitHub Actions result for the exact branch head is inspected. PostgreSQL tests do not replace deterministic race coverage for every approval/job/cancellation race.
8. **Stage 4 regression:** the Stage 4 UI visual system is retained, but its former one-click direct simulation flow is now approval-gated. Regression and owner review must confirm the new blocked/approval UX is acceptable.

## Owner decisions still open

- **OD-003:** Does every A2 synthetic run require human approval?
- **OD-015:** Which roles may approve, what separation of duties is required, who owns emergency stop, and what revocation UX is required?
- **OD-004:** Current implementation uses PostgreSQL-backed records and SQL row locks; no external workflow engine or broker was added. Confirm whether the synchronous bounded runner is acceptable or a worker loop is required before completion.
- **OD-010:** Retention/deletion remains undecided; this implementation preserves audit and mission history by default.

## Acceptance checklist

- [ ] All 19 states and every allowed/forbidden transition pass tests.
- [ ] Existing simulation and Origo routes cannot bypass lifecycle, approval, or terminal-state enforcement.
- [ ] Approval expiry, revocation, changed digest/scope, and atomic consumption tests pass.
- [ ] Duplicate submission and concurrent worker-claim tests pass against PostgreSQL 16.
- [ ] Lease expiry/restart does not reassign work while termination is uncertain.
- [ ] Cancellation, partial evidence, and stop acknowledgement are demonstrated end-to-end.
- [ ] Workspace authorization covers mission, approval, job, evidence, verification, and report operations.
- [ ] Audit records are complete and secret-safe.
- [ ] Full backend suite, PostgreSQL 16 suite, frontend build, and Playwright checks pass on the exact branch head.
- [ ] Stage 4 UI and Origo/report behavior have regression evidence.
- [ ] CI evidence and final commit SHA are recorded.
- [ ] OD-003 and OD-015 remain explicit until the owner decides; no production deployment or merge to main is performed.

**Current verdict:** substantial Stage 5 foundation committed; **not complete and not ready to merge** until the above gaps and CI evidence are resolved.
