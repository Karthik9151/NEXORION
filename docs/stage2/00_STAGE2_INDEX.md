# Stage 2 — Application Foundation

**Branch:** `stage2`  
**Scope:** First executable backend foundation corresponding to roadmap Phase 1.  
**Status:** Implemented on the Stage 2 branch; review and CI acceptance are still required. This status does not imply production readiness.

## Delivered artifacts

- `backend/app/` — FastAPI application factory, validated settings, SQLAlchemy models, authentication/session helpers, request dependencies, structured errors, and versioned routes.
- `backend/alembic/` — initial relational schema migration.
- `backend/tests/` — repeatable API tests using isolated SQLite databases.
- `.github/workflows/backend-ci.yml` — backend tests and static checks for pull requests and pushes.
- `backend/README.md` — local setup, migration, API walkthrough, configuration guards, and current limits.

## Implemented capability boundary

1. Email/password account registration and login for local development.
2. Argon2 password hashes; opaque random sessions stored as hashes; expiration and logout revocation.
3. HTTP-only session cookie, separate CSRF cookie/header check for writes, conservative cookie settings, and no credential response fields.
4. Personal workspace creation, server-side membership authorization, and opaque 404 behavior for unauthorized workspace/mission access.
5. Versioned `/v1` API; mission draft create/list/read endpoints; strict request models; explicitly synthetic-only scope; state cannot be supplied by a client.
6. PostgreSQL-compatible data models and Alembic migration; SQLite only as a local/test convenience.
7. Request/correlation IDs, sanitized validation errors, consistent error envelopes, safe health/readiness responses, baseline security headers, and initial audit events.

## Explicitly not implemented

The Stage 2 foundation does not implement digital-world entities/relationships, baseline snapshots, mission transition commands, simulation execution, idempotent run dispatch, evidence and reports, Origo verification, NEXARCH agent orchestration, model-provider integration, live event transport, frontend, deployment, or any lab/live-system access.

## Owner decisions kept open

The implementation uses a local account/session adapter to test server-side identity, but it does not settle SSO/OIDC, MFA, recovery, production account provisioning, deployment topology, retention, or external model providers. In production configuration, self-registration is disabled. A supported administrator/invitation bootstrap must be designed before production rollout.

The metadata database direction is PostgreSQL-compatible. SQLite appears only for local development and automated tests; production schema changes must use Alembic migrations.

## Acceptance evidence

The executable tests cover registration/session setup, draft mission create/list/read, cross-workspace denial, CSRF enforcement, rejection of non-synthetic scope, rejection of client-supplied state, logout revocation, request IDs, and health/readiness. CI results must be checked on the pull request before this stage is treated as verified.

The current automated suite contains 13 tests. Pull-request CI runs the suite and Ruff static checks under Python 3.11 and 3.12.
