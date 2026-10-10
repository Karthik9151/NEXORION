# NEXORION API — Stage 3 digital-world and simulation foundation

This directory contains the executable API foundation: server-side identity sessions, workspace-scoped missions, a synthetic digital-world graph, versioned baseline snapshots, deterministic registered-fixture simulations, provenance-linked evidence, structured errors, audit events, migrations, and tests.

## Status and boundaries

This is a reviewable vertical slice, not a complete NEXORION system. The general mission lifecycle API, full independent Origo verifier, model-backed agent orchestration, durable worker queue, live telemetry transport, frontend, and lab runner are not implemented. The fixed simulation endpoint performs a bounded server-side state transition for the one synthetic run path; clients still cannot set mission state.

The credential/session adapter is an initial local account implementation to make the authorization boundary testable. SSO/OIDC, MFA, account recovery, invitation/administrative provisioning, production identity ownership, and deployment topology remain owner decisions. Do not expose a production deployment until these choices and an approved account-provisioning path are resolved.

All mission scopes accepted by this stage must explicitly use synthetic_only. No network, host-command, credential-attempt, or live-system execution endpoint exists.

## Stage 3 digital-world and simulation walkthrough

The API exposes these workspace-authorized routes:

- POST and GET /v1/world/entities
- POST and GET /v1/world/relationships
- POST and GET /v1/missions/{mission_id}/baselines
- POST /v1/missions/{mission_id}/simulate
- GET /v1/missions/{mission_id}/runs

Create the mission with autonomy_tier set to simulate_synthetic, scope.mode set to synthetic_only, and the intended registered scenario ID included in scope.scenario_ids. Capture a baseline before requesting a run. Mutating requests require the CSRF cookie value in X-CSRF-Token and the authorized workspace ID in X-Workspace-ID. Simulation requests also require an Idempotency-Key of 8–128 safe characters.

The only registered scenarios are scenario-auth-failure-v1 and scenario-auth-benign-control-v1. The first should return suspicious_auth_pattern under the teaching rule; the control should return repeated_auth_failures. A completed result refers only to synthetic fixture data. Verification currently means fixed-fixture assertion checks and must not be interpreted as evidence about a live service.

~~~bash
# After registering and saving cookies.txt, set WORKSPACE_ID to the returned workspace ID.
curl -i -b cookies.txt -X POST http://127.0.0.1:8000/v1/missions \
  -H 'Content-Type: application/json' \
  -H "X-Workspace-ID: $WORKSPACE_ID" \
  -H "X-CSRF-Token: $CSRF_TOKEN" \
  -d '{"objective":"Investigate synthetic authentication failures","scope":{"mode":"synthetic_only","scenario_ids":["scenario-auth-failure-v1"],"entity_ids":[],"excluded_targets":["all external systems","all real credentials"]},"autonomy_tier":"simulate_synthetic"}'

# Replace MISSION_ID with the returned mission ID.
curl -i -b cookies.txt -X POST "http://127.0.0.1:8000/v1/missions/$MISSION_ID/baselines" \
  -H "X-Workspace-ID: $WORKSPACE_ID" -H "X-CSRF-Token: $CSRF_TOKEN"

curl -i -b cookies.txt -X POST "http://127.0.0.1:8000/v1/missions/$MISSION_ID/simulate" \
  -H "Content-Type: application/json" -H "X-Workspace-ID: $WORKSPACE_ID" \
  -H "X-CSRF-Token: $CSRF_TOKEN" -H "Idempotency-Key: stage3-manual-run-001" \
  -d '{"scenario_id":"scenario-auth-failure-v1"}'
~~~

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
