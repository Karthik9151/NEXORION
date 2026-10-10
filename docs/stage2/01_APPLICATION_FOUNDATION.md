# Stage 2 Application Foundation — Technical Notes

## Runtime layout

- **API:** FastAPI, Pydantic request/response contracts, versioned route namespace `/v1`.
- **Persistence:** SQLAlchemy 2.x; PostgreSQL is the intended shared/deployed relational store. SQLite is used for development or tests only.
- **Schema evolution:** Alembic migration `0001_initial` defines users, workspaces, memberships, hashed sessions, mission drafts, and audit events.
- **Identity adapter:** app-managed email/password login for the first local implementation. Passwords are Argon2-hashed. The browser receives an opaque random session token; only its SHA-256 digest is persisted.
- **Authorization:** each mission read/list/write validates membership on the server. `X-Workspace-ID` selects a workspace but does not authorize it.
- **API errors:** stable error-envelope response with code, message, details, retryability, and request_id. Validation responses omit submitted values.
- **Operational endpoints:** `/health` reports process health; `/ready` verifies database reachability without revealing connection strings or internals.

## Mission contract subset implemented now

A mission includes an immutable UUID-style identifier, schema version, workspace, requester, objective, scope, autonomy tier, draft state, version, and timestamps. The initial write endpoint rejects unknown fields and accepts only `scope.mode = synthetic_only`. The initial API only persists drafts; no mission state-transition endpoint exists yet.

## Security behavior

- Passwords are never stored in plaintext or returned in API responses.
- Sessions are random, opaque, database-backed, expiry-limited, and revocable.
- Session cookies are `HttpOnly`; production settings require `Secure` cookies. Mutating cookie-authenticated routes require the CSRF cookie value in `X-CSRF-Token`.
- Browser CORS is not enabled globally; add it only when a frontend origin is selected and tested.
- Unknown request fields are rejected. API validation errors do not echo rejected input values.
- Workspace and mission misses use 404 responses to avoid revealing cross-workspace resource existence.
- The initial mission schema cannot switch to `observed`, real credentials, or live targets. There is no runner or network/host-execution capability exposed through the API.
- Production mode rejects SQLite, insecure session-cookie configuration, and open self-registration; it also disables interactive docs.

## Known gaps and next stage

Before a production release: decide and implement account bootstrap/invitations and identity federation/MFA policy; add auth rate limiting and abuse controls; add dependency/security scans and PostgreSQL integration tests; review session/cookie and CSRF policy against the actual frontend origin; add database backup/restore validation, secret management, audit retention policy, and deployment threat modeling.

Next feature stages should build the digital-world entity/relationship model and baseline snapshots, then the deterministic synthetic authentication-failure scenario, evidence provenance, independent verification, and mission state machine. The existing API must not be expanded to lab or live-system actions before the planned governance and isolation gates are implemented and tested.
