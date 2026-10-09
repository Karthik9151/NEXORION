# NEXORION API — Stage 2 application foundation

This directory contains the first executable application foundation: server-side identity sessions, workspaces, persistent mission drafts, structured errors, audit events, PostgreSQL-compatible storage, migrations, and tests.

## Status and boundaries

This is a foundational implementation, not a complete NEXORION system. It does not implement the digital-world graph, synthetic scenario runner, lifecycle transitions, agent orchestration, independent verifier, lab runner, live telemetry, or frontend. Mission records can be created and read as draft; clients cannot set mission state.

The credential/session adapter is an initial local account implementation to make the authorization boundary testable. SSO/OIDC, MFA, account recovery, invitation/administrative provisioning, production identity ownership, and deployment topology remain owner decisions. Do not expose a production deployment until these choices and an approved account-provisioning path are resolved.

All mission scopes accepted by this stage must explicitly use synthetic_only. No network, host-command, credential-attempt, or live-system execution endpoint exists.

## Local development

Requirements: Python 3.11 or newer.

`bash
cd backend
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e '.[test]'
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
`

On Windows, copy .env.example to .env instead of using cp. The default .env.example uses a local SQLite database only for simple development. For shared or production-like deployments, configure PostgreSQL using a private connection URL supplied through the environment; never commit database credentials.

Interactive OpenAPI docs are available at /docs outside production mode. Process health is /health; database readiness is /ready. Equivalent versioned endpoints are /v1/health and /v1/ready.

## API walkthrough

Register a local account to create a personal workspace. The server returns the user and workspace IDs and sets an HTTP-only session cookie plus a separate CSRF cookie. Do not copy the session token into request JSON or logs.

`bash
curl -i -c cookies.txt -X POST http://127.0.0.1:8000/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"researcher@example.test","password":"Replace-this-with-a-long-password-123!","workspace_name":"My Research Workspace"}'
`

Read /v1/auth/me with the saved cookie jar to inspect the signed-in identity and authorized workspace list. For state-changing cookie-authenticated requests, copy the nexorion_csrf cookie value into the X-CSRF-Token request header and send the authorized workspace ID in X-Workspace-ID.

`bash
curl -i -b cookies.txt -X POST http://127.0.0.1:8000/v1/missions \
  -H 'Content-Type: application/json' \
  -H 'X-Workspace-ID: <workspace-id-from-register-response>' \
  -H 'X-CSRF-Token: <value-of-nexorion_csrf-cookie>' \
  -d '{"objective":"Investigate synthetic authentication failure events","scope":{"mode":"synthetic_only","scenario_ids":["scenario-auth-failure-v1"],"entity_ids":[],"excluded_targets":["all external systems","all real credentials"]},"autonomy_tier":"observe_explain"}'
`

Never use real credentials in the examples. The workspace header is only a selector: every request is checked against server-side membership. A client-provided workspace ID never grants access by itself.

## Migrations and tests

Apply schema migrations from this directory:

`bash
alembic upgrade head
`

Run the test suite:

`bash
pytest
`

Optional static lint checks:

`bash
ruff check app tests alembic
`

Tests use an isolated SQLite database. SQLite compatibility in tests does not replace PostgreSQL integration, concurrency, backup/restore, or production security testing.

## Production configuration guard

When APP_ENV=production, startup configuration validation requires PostgreSQL, SESSION_COOKIE_SECURE=true, and ALLOW_SELF_REGISTRATION=false. API documentation endpoints are disabled. Because this foundation does not yet include a production account bootstrap or invitation workflow, production rollout remains blocked until that is designed and authorized.

No licence, deployment provider, identity federation provider, data-retention term, or production SLO is implied by this implementation.
