# Technology Stack and Decision Status

**Reviewed:** 10 October 2026  
**Scope:** repository files on `stage4-implementation`, plus the uploaded Technology Cross-Check, Deployment Plan and Owner Report.  
**Cost rule:** development, tests, and planned implementation must remain at **$0 out-of-pocket**. The presence of a dependency or proposal is not evidence of a working integration.

## Verified repository technologies

| Area | What the branch contains | Status and qualification |
|---|---|---|
| Frontend | React 18.3, TypeScript 5.7, Vite 6; `@xyflow/react` 12.4; Lucide icons | Present in `frontend/package.json`; production build and Playwright E2E are recorded as passing for the Stage 4 code-bearing commit. Recheck the final PR-head run before merge. |
| Browser tests | Playwright / Chromium | `test:e2e` script and Stage 4 browser workflow exist. The E2E suite uses a disposable SQLite database. |
| Backend API | FastAPI, Uvicorn, Pydantic Settings | Present in `backend/pyproject.toml` and the application code. |
| Persistence and migration | SQLAlchemy 2, Alembic, psycopg 3 | Present in the backend manifest and migrations. PostgreSQL 16 migration/API integration checks are in CI. |
| Local test database | SQLite | Used by the normal API test suite and E2E test setup. It is useful for fast tests but does not substitute for the entire API suite and race/concurrency coverage on PostgreSQL 16. |
| Authentication and controls | Argon2 password hashing, server-side sessions, HTTP-only session cookie, CSRF cookie/header, workspace authorization | Implemented in the API foundation; production owner provisioning/bootstrap is not present in the reviewed branch. Keep registration disabled in production until a reviewed bootstrap/invitation path exists. |
| Security and evidence | Synthetic-only registered scenarios; workspace-scoped records; Origo verification history; server-generated JSON/Markdown reports | Stage 4 acceptance notes and tests record these capabilities. This remains a synthetic research/simulation capability, not proof about live systems. |
| CI | GitHub Actions; Python 3.11/3.12, pytest, Ruff, PostgreSQL 16 service, frontend build and Playwright | Workflows exist under `.github/workflows/`. The normal API suite is SQLite-backed; PostgreSQL has migration and integration coverage but not yet a confirmed full-suite run. |

## Not implemented or still open

| Technology or capability | Current truth | Tracking decision |
|---|---|---|
| NetworkX | Not declared in the reviewed backend dependency manifest; the graph is persisted through application/database models | Do not list it as an adopted dependency unless a concrete need and tested integration are added. |
| Temporal | Not present in the dependency manifest or verified runtime | OD-004 remains open. For the $0 target, the recommended starting point is a PostgreSQL-backed state machine and lease/queue tables; do not deploy a separate workflow service just because it appears in planning notes. Owner decision is still required. |
| WebSockets / SSE | No verified transport integration in the reviewed code | OD-013 remains open. Pick the simplest transport only when UI progress requirements need it. |
| Model provider / agent framework | No provider integration verified | OD-005 and OD-008 remain open. Use deterministic fixtures and mocked model responses for tests. Do not make billable provider calls under the $0 cap. |
| Dockerfile / container image | No root `Dockerfile` was found at the expected path on this branch | Hosting image build has not been demonstrated. Add and test it only as a separate implementation task. |
| Render blueprint | No root `render.yaml` was found at the expected path on this branch | Do not describe Render deployment as configured or ready. No deployment was performed. |
| Single-origin UI + API hosting | The reviewed FastAPI entry point exposes API routes; a single-container frontend serving path was not verified | P0 hosting blocker because session/CSRF behavior requires a verified compatible origin arrangement. |
| Production owner bootstrap | Not present in the reviewed branch | P0 blocker before public production mode with self-registration disabled. |
| Frontend lint and unit-test scripts | `frontend/package.json` contains dev, build, preview and E2E scripts; no lint or unit-test script is defined | Add low-cost local/CI tooling before frontend complexity increases. |
| pip-audit, npm audit, secret scanning | Not verified as enabled end-to-end by the inspected files | Add/enable free repository-native checks, and verify repository security settings; do not claim protection solely from a checklist. |
| OpenTelemetry, Kafka/Redpanda, graph database, Three.js | Proposed or deferred; not verified as installed or used | Keep deferred until measured requirements justify their cost and complexity. |

## Zero-cost implementation policy

1. Use local development, local tests, and the existing GitHub Actions workflows as the primary engineering loop.
2. Do not create paid cloud resources, paid CI plans, paid domains, commercial model API usage, paid add-ons, backup products, or an always-on worker under the current budget.
3. Do not attach a payment card to Render or create an AWS account/resource for this project while the $0 cap is active.
4. A hosted smoke test on a free Render service and free Neon database is optional—not a completion requirement—and may proceed only after free-tier availability, limits, region/data handling, and billing settings are rechecked. If the no-card / no-charge conditions cannot be established, skip the hosted test and record it as blocked by the cost limit.
5. Use mocked model calls for Stage 6 development and CI unless a provider can be used without charge under terms the owner has reviewed. Do not put keys in frontend code or commit secrets.
6. Keep Stage 7 lab execution offline and deferred. Do not provision a lab or use a PaaS for lab isolation.
7. Re-check provider prices and limits at the moment of any proposed hosted test; this document is not a promise that free tiers never change.

## Decision references

- **OD-004:** workflow runtime remains open; the PostgreSQL-backed state-machine approach is the cost-conscious recommendation, not an owner-approved final selection.
- **OD-005:** typed role interfaces first; no separate agent framework unless the acceptance criteria justify it.
- **OD-008:** model provider and model-data policy remain open; mock providers by default for testing.
- **OD-009:** deployment topology remains open, with a hard $0 spending ceiling. Local + CI is the default; hosted free-tier smoke testing is optional and must not require a card.
- **OD-013:** event transport remains open.
- **OD-011:** license, contribution/support commitments, and vulnerability disclosure policy remain owner decisions.

## Evidence standard

A technology or capability may be called implemented only when the relevant repository code/configuration exists **and** the intended behavior has verification evidence. A plan, dependency name, deployment table, diagram, or unchecked owner checklist is not implementation evidence. The authoritative task status and exit criteria live in [the implementation tracker](stage4/03_IMPLEMENTATION_TRACKER.md); Stage 4 automated evidence and limits are in [the Stage 4 acceptance record](stage4/02_ACCEPTANCE_AND_SECURITY_STATUS.md).
