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
- Automated desktop/mobile browser interaction and horizontal-overflow checks pass. A human visual review against the design board and a hosted smoke test remain recommended pre-production release gates; they have not been performed in this environment.
- Branch-protection enforcement is not assumed. A green workflow is evidence of a completed check, not proof that GitHub prevents a bypass merge.

## Release decision

Merge Stage 4 only after the final pull-request head has green Frontend CI (build and browser E2E), green Backend CI (Python checks and SQLite/PostgreSQL migration/API checks), and a completed source-level security/diff review. The hosted smoke test and human visual sign-off remain required before describing the deployed product as production-released.

### Final run record

**Code-bearing acceptance commit:** `bdefa1c71da347dff9ad1f1d55696f1188e13fb3`  
**Recorded:** 10 October 2026

- **Frontend TypeScript/production build: PASS** — [Frontend CI run](https://github.com/Karthik9151/NEXORION/actions/runs/38034621769).
- **Chromium end-to-end suite: PASS** — [Frontend CI run](https://github.com/Karthik9151/NEXORION/actions/runs/38034621769). Coverage includes invalid-login handling, registration, switching between authorized workspace memberships, workspace-scoped graph writes, a registered synthetic simulation, persisted ORIGO verification, server-generated report preview, and mobile navigation/overflow.
- **Backend tests and Ruff on Python 3.11: PASS** — [Backend CI run](https://github.com/Karthik9151/NEXORION/actions/runs/38034621760).
- **Backend tests and Ruff on Python 3.12: PASS** — [Backend CI run](https://github.com/Karthik9151/NEXORION/actions/runs/38034621760).
- **SQLite migration, PostgreSQL migration and API integration, and PostgreSQL downgrade/re-upgrade: PASS** — [Backend CI run](https://github.com/Karthik9151/NEXORION/actions/runs/38034621760).
- **Source-level security review:** workspace membership, CSRF, scoped entity/relationship access, synthetic-only scenarios, verification-history consistency, and workspace-scoped reports were inspected alongside the automated tests.
- **Hosted deployment smoke test / human visual review of the deployed service: NOT RUN.** This environment did not authenticate to or exercise a hosted NEXORION deployment. Complete these checks before describing the service as production-released.

The latest code-bearing commit had all required automated CI checks green. The acceptance-document and workflow-filter updates also trigger a fresh PR-head CI run; merge remains gated on those fresh checks.

## Acceptance recheck — 10 October 2026, PR #16

This recheck is additive to the historical Stage 4 record above. It refers to the Stage 4/5 acceptance-fix branch, not to `main` or to a production release.

**Code-bearing commit checked:** `f988447188f15a106f894049fc578e16bbf1c75c`

- **Frontend production build: PASS** — [Frontend CI run #105](https://github.com/Karthik9151/NEXORION/actions/runs/38051448500).
- **Playwright/Chromium: PASS, 4/4 tests** — same run. Coverage: safe invalid-login feedback; registration, workspace isolation, graph, approval gate, reporting and mobile navigation; persisted Origo verification; session persistence, CSRF denial and logout revocation.
- **Production container build / non-root runtime assertion: PASS** — same run; configured image user is `nexorion`.
- **Backend tests and Ruff: PASS on Python 3.11 and 3.12; SQLite migration round-trip: PASS; PostgreSQL 16 full API suite and migration downgrade/re-upgrade: PASS** — [Backend CI run #195](https://github.com/Karthik9151/NEXORION/actions/runs/38051447065).
- **Read-only public staging checks: PASS for the environment observed separately** — the deployed `main` service served `/`; `/health` returned `{"status":"ok"}`; `/ready` and `/v1/ready` returned `{"status":"ready"}`; unauthenticated `GET /v1/auth/me`, `GET /v1/missions`, and `GET /v1/scenarios` returned `401`. These checks do not prove a signed-in hosted session or that the PR branch is deployed.
- **Hosted authenticated browser test / human visual and accessibility sign-off: NOT RUN.** No signed-in staging browser profile or test credentials were available. Do not represent these as passed.

**Stage 4 verdict:** the automated regression gates pass on this PR head. Full deployed acceptance remains conditional on a signed-in staging check, human visual/accessibility review, and final PR-head CI after any further changes. Keep PR #16 in draft and do not merge on the basis of this record alone.
