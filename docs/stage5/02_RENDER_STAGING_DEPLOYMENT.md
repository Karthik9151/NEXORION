# Stage 5 Render staging deployment

This branch packages the NEXORION web app as a single Docker service on Render. The Vite frontend is built into the image and served by FastAPI on the same origin, so browser API requests and HTTP-only session cookies use the same host.

## Required external configuration

1. **Use a dedicated PostgreSQL database for NEXORION staging.** The current Render workspace already has its one active Free Render PostgreSQL database assigned to IESP. Do not point NEXORION at IESP's database or suspend IESP to make room. Under the current $0-spend constraint, use a separate free PostgreSQL provider such as Neon; a separate Render PostgreSQL database requires a plan/availability change and must not be created if it incurs a charge without explicit approval.
2. In the Render service's **Environment** settings, set `DATABASE_URL` to the actual direct or pooled connection string for that dedicated database. The scheme must be `postgresql+psycopg://`. Preserve the provider's actual hostname, numeric port, database name, username, and password. Never use placeholders such as `HOST`, `PORT`, `USER`, or `PASSWORD` as literal values. URL-encode reserved characters in credentials if required by the provider.
3. Set `APP_ENV=production`, `SESSION_COOKIE_SECURE=true`, `ALLOW_SELF_REGISTRATION=false`, and keep `CORS_ALLOWED_ORIGINS` empty for this same-origin deployment.
4. Set `NEXORION_BOOTSTRAP_OWNER_EMAIL` to the authorized initial owner's email and `NEXORION_BOOTSTRAP_OWNER_PASSWORD` to a strong, unique staging password using Render's secret environment-variable UI. Never commit either value.
5. The first container startup runs Alembic migrations and then `python -m app.bootstrap_owner`. On an empty database, this creates the initial owner and workspace; if any user already exists, it skips creation. Confirm the logs show successful owner creation and then remove both bootstrap variables from Render and redeploy/restart. Do not enable public self-registration as a workaround.
6. The Render Blueprint uses `/health` for process health. `/ready` checks database readiness. After deployment, verify both endpoints and check the logs for migration and bootstrap success.
7. Render's Free web service may sleep while idle. Treat this as staging, not as a production SLA.

## Container behavior

- Frontend assets are built in the Node 20 stage.
- Python dependencies are installed from root `requirements.txt`, which points to the canonical `backend/pyproject.toml` project metadata.
- Alembic migrations run at container startup before Uvicorn starts.
- FastAPI serves the built frontend and API on the same origin; production frontend requests use same-origin `/v1` routes while local Vite development uses the `/api` proxy.
- Database URLs, database passwords, and bootstrap secrets belong only in the hosting provider's secret environment settings, never in Git.

## npm lockfile

Generate and commit `frontend/package-lock.json` from the exact `frontend/package.json` using Node.js 20 and npm in a network-enabled environment:

```bash
cd frontend
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
npm ci
npm run build
```

Commit the generated lockfile only after `npm ci` and the build pass. The deployment Dockerfile currently uses `npm install` because no verified lockfile was present when this branch was prepared.
