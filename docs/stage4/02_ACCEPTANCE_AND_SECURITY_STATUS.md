# Stage 4 — Acceptance and Security Verification

**Working branch:** `stage4-implementation`  
**Target base:** `main`  
**Scope:** UI/UX integration, authenticated API integration, workspace isolation, synthetic-only simulation, ORIGO verification, and report generation.

## Acceptance gates

| Gate | Evidence | Release rule |
| --- | --- | --- |
| Frontend production build | Frontend CI runs `npm run build` (TypeScript plus Vite production build). | Must pass on the final pull-request head. |
| Backend tests and static checks | Backend CI runs pytest and Ruff on Python 3.11 and 3.12. | Must pass on the final pull-request head. |
| Database compatibility | Backend CI applies fresh SQLite and PostgreSQL migrations, exercises the API against PostgreSQL, and checks downgrade/re-upgrade. | Must pass on the final pull-request head. |
| Browser end-to-end | Playwright/Chromium suite covers invalid-login handling, registration, authorized workspace switching, graph writes, a registered synthetic simulation, ORIGO verification, server report preview, mobile navigation, and horizontal overflow. | Must pass on the final pull-request head. |
| Workspace security | Backend tests cover workspace-scoped reports; the browser suite verifies visible graph records do not cross authorized workspace selection. | Review both the server-side authorization checks and browser behavior. |
| Security boundary | Only registered synthetic fixtures are executable; sample data stays browser-local; simulation completion is distinct from a persisted ORIGO verdict. | Do not enable live-target, external-network, shell, or credential execution as part of Stage 4. |

## Browser test environment

The browser suite uses a disposable SQLite database at `/tmp/nexorion-stage4-e2e.db`. CI applies migrations before tests. The fixture script creates a second workspace membership directly in that disposable database so the UI can exercise actual workspace switching; it does not introduce a test or administrative API route. Never configure this suite to use a production or shared database.

Run from the repository root after installing the project dependencies:

```bash
cd backend
DATABASE_URL=sqlite:////tmp/nexorion-stage4-e2e.db APP_ENV=test alembic upgrade head
cd ../frontend
npm install
npx playwright install chromium
APP_ENV=test DATABASE_URL=sqlite:////tmp/nexorion-stage4-e2e.db NEXORION_API_ORIGIN=http://127.0.0.1:8000 npm run test:e2e
```

Stop other services using ports 8000 or 4173 before running locally.

## Known limits

- Passing automated tests validate the synthetic fixture workflows and application contracts, not real-world security research effectiveness.
- The repository does not currently provide a production deployment acceptance test or hosted browser test against a deployment; those require an approved deployment environment and credentials.
- A human review of the generated interface at desktop/mobile breakpoints and a final pull-request review remain required before merging to `main`.
- Branch-protection enforcement is not assumed. A green workflow is evidence of a completed check, not proof that GitHub prevents a bypass merge.

## Release decision

Do not merge Stage 4 until the final pull-request head has green Frontend CI (build and browser E2E), green Backend CI (Python checks and SQLite/PostgreSQL migration/API checks), and a reviewed diff. Record the final run URLs and any unresolved limitations below.

### Final run record

- Frontend build: pending final pull-request checks.
- Playwright browser suite: pending final pull-request checks.
- Backend Python 3.11 / 3.12 tests and Ruff: pending final pull-request checks.
- PostgreSQL migration/API integration: pending final pull-request checks.
- Manual hosted deployment smoke test: not run in this environment.
