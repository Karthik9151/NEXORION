# NEXORION — Implementation Tracker, $0 Deployment Plan and Owner Gates

**Last reviewed:** 10 October 2026  
**Working branch:** `stage4-implementation`  
**Target base:** `main`  
**Scope:** implementation tracking and documentation alignment only. This document update does not add runtime code, create cloud resources, deploy the app, or prove any unrun test.  
**Binding budget:** **$0 spend ceiling** as requested by the project owner.

## 1. Rules for using this tracker

This is the task-level status register. Use [Roadmap and Acceptance Criteria](../ROADMAP.md) for phase intent and [Stage 4 Acceptance and Security Verification](02_ACCEPTANCE_AND_SECURITY_STATUS.md) for its specific recorded CI evidence. Keep source requirements and existing decision records intact; resolve conflicts in the owner-decision register rather than silently changing the architecture.

Use these statuses consistently:

- **Verified** — required code/configuration exists and the listed verification evidence is green for the relevant branch/commit.
- **In progress** — implementation has begun, but the exit criteria are not all met.
- **Blocked (P0/P1)** — an unmet dependency or security/cost condition prevents safe progression.
- **Owner decision** — cannot be closed by the implementation agent without the owner’s choice.
- **Not started** — no implementation or evidence was found in the reviewed branch.
- **Deferred** — deliberately excluded from the current scope.

A plan, unchecked box, dependency name, diagram, or old green run is not evidence for a new commit. Before merge, recheck the latest pull-request head and its checks. Update status with a link to a commit, test run, source file, or a recorded owner decision.

## 2. Non-negotiable $0 cost guardrail

1. Primary path: local development, local tests, and the existing GitHub Actions workflows. Stop or move work local if a free allowance or account quota would be exceeded.
2. Do not create paid Render/AWS/database resources, paid plans, paid domains, commercial model API usage, paid CI, backup add-ons, or an always-on worker.
3. Do not attach a payment card to Render while the $0 cap is active. Do not provision AWS for this project.
4. A Render free + Neon free hosted smoke test is **optional**. It may only be attempted after current plan terms, account billing controls, data region, limits, and no-card eligibility are checked. If any of these are uncertain, do not deploy; mark the hosted test blocked by cost policy.
5. Keep Stage 6 model calls mocked and deterministic in development/CI. No provider API key should be required. Only revisit a real provider after the owner verifies that usage can remain at $0 and approves its data-retention terms.
6. Stage 7 is **not to be started**: no cloud lab, no PaaS lab, no external network, and no real targets. Its future isolated environment needs a separate threat model and owner authorization.
7. Never interpret free-tier sleep/restarts as evidence for reliable workers, durable recovery, backup, restore, or production availability. Free-tier terms can change; verify them again before optional hosting.

## 3. Status snapshot

### Stage overview

| NEXORION stage | Current recorded position | Evidence / open gate | Tracker status |
|---|---|---|---|
| Stage 1 — Blueprint and governance contracts | Blueprint and traceability documents exist; owner acceptance is still required | Walk all 13 gates in [requirement-to-test traceability](../stage1/07_REQUIREMENT_TO_TEST_TRACEABILITY.md) and record the owner decision. OD-001 through OD-015 remain open until explicitly closed. | **Owner decision / incomplete acceptance** |
| Stage 2 — API foundation | FastAPI, persistence, sessions/CSRF, workspace authorization, migrations and SQLite API tests exist | See [backend README](../../backend/README.md); production identity/onboarding is not solved by the local account adapter. | **Implemented slice; not production-ready** |
| Stage 3 — Digital world and deterministic simulation | Prior stage record cites passing Python 3.11/3.12, Ruff, SQLite migration, PostgreSQL 16 migration, and PostgreSQL API smoke checks | [Stage 3 verification run](https://github.com/Karthik9151/NEXORION/actions/runs/38026378118). Evidence applies to the named Stage 3 commit/scope, not future changes. | **Verified for bounded synthetic scope** |
| Stage 4 — UI/UX, Origo verification and reports | Acceptance record documents frontend build/E2E and backend checks passing for code-bearing commit `bdefa1c71da347dff9ad1f1d55696f1188e13fb3` | [Frontend CI](https://github.com/Karthik9151/NEXORION/actions/runs/38034621769), [Backend CI](https://github.com/Karthik9151/NEXORION/actions/runs/38034621760), and [Stage 4 acceptance record](02_ACCEPTANCE_AND_SECURITY_STATUS.md). Recheck the final PR-head CI before merge. Hosted smoke test and human visual sign-off are documented as not run. | **Automated evidence recorded; close-out pending** |
| Stage 5 — Governance and durable workflows | Not implemented as the full governance/workflow system | Complete owner decisions OD-003, OD-004 and OD-015; implement the acceptance matrix in section 7 with PostgreSQL 16 race/recovery tests. | **Not started / owner-gated** |
| Stage 6 — Bounded specialist agents | No real model-provider integration verified | Close OD-001, OD-002, OD-005 and OD-008 first. Use typed interfaces and a mocked model; no billable API calls. | **Deferred pending Stage 5 and owner decisions** |
| Stage 7 — Isolated lab | Not in scope | Close OD-006 and complete a separate threat model, isolation and emergency-stop review. No provisioning under the current plan. | **Deferred — do not start** |
| Stage 8 — Operations hardening | No production release posture established | Define free local/CI operational checks; do not claim backup/restore or availability without evidence. Release policy in OD-011 remains owner-controlled. | **Later gate** |

### Hosting and readiness blockers

| Key | Priority | Work item | What is known now | Exit criteria | Status |
|---|---|---|---|---|---|
| HOST-01 | P0 | Same-origin UI/API | CSRF cookie/header flow requires a verified compatible origin. Separate UI/API hosts are not assumed compatible. A single-container serving path was not verified. | Build UI assets into the backend image or deliberately design and test an approved shared-parent-domain arrangement; test login, CSRF-protected mutations, logout, and browser cookie behavior on that exact topology. | **Blocked / not implemented** |
| HOST-02 | P0 | Idempotent owner bootstrap | Production configuration disables self-registration, but a bootstrap/invitation path is not present in the reviewed code. | Bootstrap is repeatable, owner credentials arrive only through server-side environment secrets, password is Argon2-hashed, password never logged, self-registration remains off, and reruns cannot create duplicate accounts/workspaces. Add tests. | **Not started** |
| DB-01 | P0 | Full API suite on PostgreSQL 16 | Backend API tests primarily use isolated SQLite. CI has PostgreSQL migration and integration/smoke coverage, not proven full-suite concurrency coverage. | Run the full API suite on PostgreSQL 16 in CI, then add concurrent state transitions, lease expiry/revocation, duplicate requests, approval consumption races, and workspace-denial tests. Keep SQLite coverage too. | **Partial / blocks Stage 5** |
| HOST-03 | P1 | Safe container build and configuration | The expected root Dockerfile and root render.yaml returned not found on the reviewed branch. | Multi-stage build; frontend dist served by the same origin; non-root runtime; no embedded secrets; environment-only configuration; documented local build/test commands. | **Not started** |
| HOST-04 | P1 | Optional hosted smoke script | No hosted smoke evidence has been recorded. This is not required to continue free local development. | Only after a no-card free-tier eligibility check: wake/retry up to 90 seconds, then check login, mission create, baseline, simulate, verify, report, and cross-workspace denial; save redacted evidence. Skip if any charge risk exists. | **Not started / optional** |
| SEC-01 | P1 | Free CI security and frontend checks | Frontend package currently lists dev/build/preview/E2E scripts, not lint or unit-test scripts. pip-audit, npm audit, and secret scanning were not verified as enforced. | Add lint and unit-test scripts; add dependency audits and secret scanning appropriate to a public repository; document/remediate findings without exposing secrets. Any failing audit needs triage, not suppression by default. | **Not started** |
| DOC-01 | P1 | Technology/documentation alignment | README and TECH_STACK had stale claims about source/manifests and proposed technologies. This change synchronizes the docs and links this tracker. | Keep README, TECH_STACK, roadmap, acceptance records and OD-009 consistent after each merge; preserve the distinction between documented, implemented and verified. | **This documentation change** |
| GOV-01 | P1 | Public release policies | Licence and vulnerability reporting channel remain owner decisions. | Owner chooses a licence and approves SECURITY.md/reporting expectations; no licence is inferred. | **Owner decision — OD-011** |

## 4. Stage 4 close-out gate

Do not state that Stage 4 is merged or production-released based only on the recorded code-bearing commit.

- [x] Stage 4 acceptance record documents passing frontend production build.
- [x] Stage 4 acceptance record documents passing Chromium Playwright E2E for registration/login, authorized workspace switching, graph writes, synthetic simulation, Origo verification, report preview, and mobile navigation/overflow.
- [x] Stage 4 acceptance record documents backend pytest/Ruff on Python 3.11 and 3.12.
- [x] Stage 4 acceptance record documents SQLite/PostgreSQL migration checks and PostgreSQL API integration/smoke checks.
- [ ] Re-run/review the latest PR-head CI after all branch documentation and workflow-path changes; require green checks before merge.
- [ ] Owner performs a visual review of the actual UI and records any mismatches against the supplied design.
- [ ] Owner decides whether an optional hosted smoke test is worth attempting after the $0/no-card checks. A skipped hosted test does not block local/CI work.
- [ ] Record the Stage 4 merge commit only after merge actually happens. Do not invent a merge SHA.

The checked items above are **what the repository acceptance record reports**, not newly executed tests in this documentation task. The current edit has not run application tests and has not deployed anything.

## 5. Ordered implementation phases

| Work package | Purpose | Entry gate | Deliverables | Completion gate |
|---|---|---|---|---|
| WP-0 — Synchronize project records | Stop docs from overstating capabilities or costs | This tracker review | README, TECH_STACK, roadmap link, OD-009 $0 policy and evidence links aligned | Docs describe branch/CI state correctly and all unknowns stay explicit |
| WP-1 — Stage 4 close-out | Finish evidence and owner review without paid hosting | Current Stage 4 branch plus this checklist | Fresh CI status; diff/security review; owner visual review; optional no-cost smoke test decision | Latest required CI green; no unresolved release-blocking diff/security issue; merge outcome recorded honestly |
| WP-2 — Hosting readiness, only if wanted | Design a $0-compatible one-origin test deployment | Owner keeps $0 cap and decides optional hosting is worthwhile | Safe container serving UI/API at one origin; secure owner bootstrap; migration/startup approach; environment checklist; no-card proof | P0 requirements pass local tests; optional hosted test has explicit no-charge/no-card eligibility; no paid resource added |
| WP-3 — Stage 5 governance model | Preserve the Stage 1 lifecycle and authorization invariants | OD-003, OD-004, OD-015 have recorded choices; full PostgreSQL 16 suite available | State machine, plan-digest approval records, single-use consumption, fail-closed policy checks, database-backed leases, recovery and audit | Entire Stage 5 acceptance matrix passes with race tests; denial is default on unknown state |
| WP-4 — Stage 6 bounded-agent seam | Add proposal-only interfaces without granting model authority | Stage 5 gates pass; OD-001/002/005/008 are recorded | Typed task/result contracts, registry consistency, deterministic tool allowlists, mock-provider tests, traceable handoffs | Malformed/untrusted model outputs are rejected; policy is enforced outside the model; all tests work without paid model calls |
| WP-5 — Stage 7 isolated-lab design | Decide whether a lab should exist at all | OD-006 plus independent threat model and explicit later owner approval | Design only until isolation, egress controls, secrets, kill switch, cleanup and evidence are proven | No code/provisioning begins until all safety and cost requirements are reviewed; under current $0 cap, lab stays deferred |
| WP-6 — Stage 8 operational checks | Evidence-based reliability and release hygiene | Earlier required behavior is stable | dependency/security checks, observability design as justified, recovery documentation, resource limits and incident steps | Claims about operations are linked to reproducible evidence; no paid monitoring/backup service is added |

## 6. P0 implementation specifications

### P0-A — One origin for the UI and API

Recommended direction if hosting is later approved: build the Vite frontend and have FastAPI (or a deliberately configured same-origin reverse proxy) serve the built UI and versioned API from the same browser origin. Keep credentialed CORS restrictive. Prove the behavior in a real browser using the exact deployment topology before relying on it.

Required cases: unauthenticated access denied for protected routes; registration/bootstrap creates no duplicate account on retry; session cookie is HttpOnly and Secure in production; CSRF cookie is copied to X-CSRF-Token for state-changing requests; allowed requests pass; missing/mismatched token fails; logout invalidates the server session; workspace-crossing request fails. Never put server secrets in Vite/client environment variables.

### P0-B — Owner bootstrap without public self-registration

Implement an idempotent command/startup step guarded by production configuration and backed by the configured database. Read owner email, a strong password secret, and workspace name from server environment. Hash with Argon2; never log or echo the secret. Repeat execution must not create duplicate owners/workspaces and must fail safely if an existing owner conflicts. Keep ALLOW_SELF_REGISTRATION=false in production. Add tests for first run, rerun, missing/invalid secrets, and existing-account conflict.

### P0-C — PostgreSQL 16 is a first-class test backend

Keep fast SQLite tests, but also execute the complete API suite against disposable PostgreSQL 16 in CI. Add separate concurrency/race tests for duplicate mission/run requests, simultaneous state transitions, approval consumption, lease claim/renew/revoke/expiry, cancellation during queue/run, restart reconciliation, and cross-workspace denial. CI must use synthetic disposable data and must never use a hosted/production database.

## 7. Stage 5 governance and durable-workflow acceptance matrix

Source of truth: [Mission Lifecycle](../stage1/03_MISSION_LIFECYCLE.md) has **19 states**, and [Governance and Security Controls](../stage1/04_GOVERNANCE_SECURITY_CONTROLS.md) defines the trust boundaries and fail-closed rules. Preserve all state names and allowed transitions rather than inventing a shorter lifecycle.

| Work key | Acceptance requirement | Minimum automated evidence | Suggested CI suite/label key* | Stage 5 status |
|---|---|---|---|---|
| S5-LIFE-01 | Implement all 19 states: draft, validating, blocked_scope, blocked_approval, rejected, ready, planning, planned, queued, running, cancelling, verifying, succeeded, completed_with_warnings, disputed, inconclusive, failed, cancelled, expired. No direct client state writes. | Unit/API tests for all permitted transitions, forbidden transitions, terminal states, and optimistic-version conflicts. | stage5-lifecycle | Not started |
| S5-APP-01 | Approval binds workspace, requester, mission, action class, scope/constraints, canonical plan digest, expiry, decision and approver. Plan/scope edits invalidate it. | Digest mismatch, scope mutation, expired approval and wrong-workspace negative tests. | stage5-approval-binding | Not started |
| S5-APP-02 | Approval is single-use and consumed transactionally at the execution boundary; requester is not approver when segregation applies; no self-approval. | Concurrent duplicate consumption and same-principal approval race tests on PostgreSQL 16. | stage5-approval-race | Owner gate OD-015 |
| S5-POL-01 | Missing, malformed, unavailable or contradictory policy/approval/verifier results fail closed. | Policy outage and unknown-result tests prove no queue/dispatch occurs. | stage5-policy-fail-closed | Not started |
| S5-LEASE-01 | Lease claim, heartbeat, expiry, revocation and reassignment are durable. Timeout alone does not prove an old worker stopped. | Concurrent claim tests, stale lease tests, revocation-before-reassign tests and duplicate-delivery tests. | stage5-leases | Not started |
| S5-REC-01 | Cancellation is idempotent; new work stops; partial evidence is retained; restart recovery reconciles state before resuming and rechecks authorization. | Queued/running cancellation, lost worker acknowledgement, restart and unknown-execution-state tests. | stage5-cancel-recovery | Not started |
| S5-AUD-01 | Every transition records actor/service, old/new state, timestamp, reason, request/correlation ID and object version. | Audit shape/provenance tests; secret-redaction assertions. | stage5-audit | Not started |
| S5-WS-01 | Workspace authorization is checked on read, approval, cancel, queue, resume, evidence and report actions. | Two seeded test principals/workspaces; read/write/approval race denial matrix. | stage5-workspace-isolation | Not started |
| S5-PG-01 | Entire applicable API suite runs on PostgreSQL 16; SQLite remains as a fast lane. | CI records full-suite PG16 result plus explicit race/concurrency tests. | stage5-postgres16 | Blocked by DB-01 |
| S5-UI-01 | The UI displays blocked/running/cancelling/terminal states from the server; it cannot authorize or directly set workflow state. | E2E covers allowed/denied actions and refresh/reload consistency. | stage5-ui-states | Not started |

*These are proposed suite/label keys to organize future checks, not a claim that GitHub labels already exist. Create and use labels only when the team actually configures them.

## 8. Stage 6 bounded-agent entry gates

Do not start model-backed agent implementation until Stage 5's governance gates pass and OD-001, OD-002, OD-005, and OD-008 are recorded. Start with typed interfaces and deterministic modules. All agent results are untrusted proposals; policy and authorization remain deterministic software checks.

Minimum gates: bounded role schemas; versioned input/output contracts; allowlisted tool names and typed arguments; per-task capability restrictions; bounded time/retries/output size; prompt-injection and malformed-output tests; no model-generated shell/SQL/arbitrary code execution; no live URL fetch or external-target operation; explicit evidence provenance; mock-model tests by default. A missing/failed provider, malformed result or policy uncertainty must result in blocked/inconclusive, never implicit success. Paid tokens/API calls remain forbidden under the active $0 budget.

## 9. Stage 7 and Stage 8 boundaries

**Stage 7:** deferred. OD-006 and a separate threat model are mandatory before design approval. No lab runner, cloud account, external egress, real credential, live system, or PaaS lab may be provisioned under this tracker. A zero-cost local concept review is not lab authorization.

**Stage 8:** focus on reproducible CI checks, secret redaction, dependency audits, documented configuration, quotas, and evidence-backed recovery expectations. Do not claim backup/restore unless a tested backup/restore procedure exists. Do not add a paid observability, backup or monitoring service.

## 10. Owner decision checklist

### Current / before any hosting
- [ ] Walk and record the Stage 1 13-item acceptance gate in [requirement-to-test traceability](../stage1/07_REQUIREMENT_TO_TEST_TRACEABILITY.md).
- [ ] Recheck the latest Stage 4 PR-head CI and complete source/diff review; record the actual merge SHA only after merge.
- [ ] Review the UI against the approved design and record the human visual sign-off.
- [ ] Confirm whether to skip the optional hosted smoke test (recommended default under a strict $0 budget); if attempted, verify no-card free eligibility first.
- [ ] Approve or revise the proposed one-origin topology and environment-driven owner bootstrap before those code changes begin.
- [ ] Keep the $0 cap active: no payment card, paid cloud resources, paid model API calls, or paid plan changes.

### Before Stage 5
- [ ] OD-003 — choose the synthetic-run human-approval policy. Recommended default: deterministic scope/policy validation always; human approval configurable and mandatory for any future lab tier.
- [ ] OD-004 — choose workflow runtime. Recommended default for $0: PostgreSQL-backed state machine and leases; do not add Temporal or a separate broker unless evaluated requirements justify their operating burden and costs.
- [ ] OD-015 — define approver roles, requester/approver separation, emergency-stop owner and revocation UX. Tests may use two seeded test identities; that does not imply two real operators exist.

### Before Stage 6
- [ ] OD-001 / OD-002 — confirm canonical authority hierarchy and role aliases.
- [ ] OD-005 — approve typed interfaces first or document why a framework is necessary.
- [ ] OD-008 — approve provider/data policy only if a no-charge, appropriately governed option is established; otherwise retain mocked model calls.

### Before Stage 7 or public/real users
- [ ] OD-006 — separate lab design and threat model; Stage 7 stays paused.
- [ ] OD-007 / OD-010 / OD-011 / OD-012 / OD-013 — record identity, retention, release-policy, operational objective and event-transport decisions before the scope requires them.

## 11. Links and reporting cadence

- [Stage 4 acceptance and security record](02_ACCEPTANCE_AND_SECURITY_STATUS.md)
- [Technology stack cross-check](../TECH_STACK.md)
- [Canonical roadmap](../ROADMAP.md)
- [Open owner decisions](../stage1/08_OPEN_DECISIONS.md)
- [Mission lifecycle and recovery rules](../stage1/03_MISSION_LIFECYCLE.md)
- [Governance and security controls](../stage1/04_GOVERNANCE_SECURITY_CONTROLS.md)
- [Requirement-to-test traceability](../stage1/07_REQUIREMENT_TO_TEST_TRACEABILITY.md)

Update this file on each implementation PR: record status transitions, the exact commit/CI run that supports each “Verified” entry, remaining owner decisions, and any new cost or safety blockers. If verification cannot be run without payment, do not pay; record the gate as blocked by the $0 budget and propose a local/CI alternative.
