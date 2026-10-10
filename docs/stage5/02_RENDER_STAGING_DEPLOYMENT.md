# Stage 5 Render staging deployment

This deployment branch adds a root Dockerfile, Render Blueprint, and root Python requirements entry point. It builds the Vite UI and serves it from FastAPI on the same origin, so browser API requests and HTTP-only session cookies use the same host.

## Before deploying

1. Create a separate Neon PostgreSQL database for staging. Use PostgreSQL 16 compatibility.
2. Copy its pooled or direct connection string into Render's `DATABASE_URL` environment variable, changing the scheme to `postgresql+psycopg://` if the provider supplied `postgresql://`.
3. Keep `APP_ENV=production`, `SESSION_COOKIE_SECURE=true`, and `ALLOW_SELF_REGISTRATION=false`.
4. The current application does not yet provide a production owner/bootstrap workflow. A production-mode deployment therefore must not be considered usable until an authorized initial-owner provisioning path is implemented and tested. Do not enable public self-registration as a shortcut.
5. The Render Blueprint uses `/health` for process health. `/ready` checks database connectivity.
6. Render's free web service may sleep while idle. Use staging only; do not treat it as a production SLA.

## Container behavior

- Frontend assets are built in the Node 20 stage.
- Python dependencies are installed from root `requirements.txt`, which points to the canonical `backend/pyproject.toml` project metadata.
- Alembic migrations run at container startup before Uvicorn starts.
- FastAPI serves the built frontend and API on the same origin; production frontend requests use same-origin `/v1` routes while local Vite development uses the `/api` proxy.
- No Neon credentials or bootstrap secrets belong in the repository.

## npm lockfile

Generate and commit `frontend/package-lock.json` from the exact `frontend/package.json` using Node.js 20 and npm in a network-enabled environment:

```bash
cd frontend
npm install --package-lock-only --ignore-scripts --no-audit --no-fund
npm ci
npm run build
```

Commit the generated lockfile only after `npm ci` and the build pass. The deployment Dockerfile currently uses `npm install` because no verified lockfile was present when this branch was prepared.
