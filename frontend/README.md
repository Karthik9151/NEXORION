# NEXORION Frontend

React + TypeScript + Vite interface for the NEXORION Synthetic Cyber Research Platform.

## Included workspaces

- Mission Center — workspace-scoped mission list, lifecycle and synthetic mission creation.
- Digital World Explorer — interactive React Flow canvas for typed synthetic entities and relationships.
- Simulation Lab — the API-backed catalog of registered synthetic scenarios and persisted run history.
- Evidence & Origo — evidence provenance, SHA-256 digests, independently calculated Origo verification and persisted verification history.
- Mission Reports — server-generated Markdown/JSON reports and a preview from persisted mission, baseline, run, evidence and verification records.
- Settings — dual themes, session context, API connectivity and explicit safety boundaries.

## Themes

The default Obsidian Gold theme uses dark surfaces and champagne/gold accents. Polar Minimalist switches the same architecture to white/slate surfaces and technical orange accents. The environment banner remains visible across the workspaces.

## Run locally

Requirements: Node.js 20+ and npm, plus the FastAPI backend.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api/*` to `http://localhost:8000` by default. Override its target with `NEXORION_API_ORIGIN`. Register or sign in to load persisted data. The sample environment is an explicit UI-only preview: its data and actions remain in browser memory and cannot request real verification or server reports.


## Browser end-to-end validation

The Stage 4 acceptance suite uses Playwright with Chromium and a disposable SQLite database. It exercises invalid-login error handling, registration, selection between two authorized workspace memberships, workspace-scoped graph writes, the registered synthetic simulation flow, persisted Origo verification, server-generated report preview, and mobile navigation/overflow.

CI installs the backend test dependencies, applies migrations to `/tmp/nexorion-stage4-e2e.db`, installs Chromium, and runs the browser suite. The multi-workspace fixture helper writes only to the disposable test database; it is not an application endpoint.

To run locally after installing the backend and frontend dependencies, stop any existing server on ports 8000 and 4173, then run:

```bash
# From the repository root
cd backend
DATABASE_URL=sqlite:////tmp/nexorion-stage4-e2e.db APP_ENV=test alembic upgrade head
cd ../frontend
npm install
npx playwright install chromium
APP_ENV=test DATABASE_URL=sqlite:////tmp/nexorion-stage4-e2e.db NEXORION_API_ORIGIN=http://127.0.0.1:8000 npm run test:e2e
```

The suite creates a test account and records in that disposable database. Do not point it at a production or shared database.

## Stage 4 API integration

The frontend's typed client calls these API contracts under `/v1`:

- `GET /scenarios` — registered executable synthetic scenarios only.
- `POST /missions/{mission_id}/runs/{run_id}/verify` — request a persisted Origo attempt.
- `GET /missions/{mission_id}/runs/{run_id}/verification` — verification history and latest attempt.
- `GET /missions/{mission_id}/report` — structured JSON report from persisted records.
- `GET /missions/{mission_id}/report.md` — server-generated Markdown report.

Missions, simulation execution and Origo verification have separate status dimensions. Successful simulation is never displayed as a persisted Origo verdict unless verification history actually contains that verdict. Planned scenario placeholders are not sent to the backend as executable operations.

## Deployment configuration

For a separately hosted frontend, set `VITE_API_BASE_URL` to the backend API origin prefix, for example `https://your-api.example.com`. Configure backend `CORS_ALLOWED_ORIGINS` to exact trusted frontend origins, comma-separated as needed; wildcard origins with credentialed cookies are rejected. Production session cookies must be secure. Do not place secrets in `VITE_` variables.

When the frontend and backend share one origin, prefer a same-origin reverse proxy. The session cookie remains HTTP-only; the frontend reads only the separate CSRF cookie and passes its value in the mutation header.

## Security and interpretation boundaries

- Every mutation uses the backend CSRF cookie value where available and the workspace header for workspace-scoped routes.
- Mission creation fixes scope to `synthetic_only`, excludes real systems/external networks, and requests `simulate_synthetic`.
- The UI does not implement target scanning, shell execution, real credential handling, or live-system mutation.
- The catalog contains only registered inert synthetic scenarios. Other scenario cards are explicitly planned placeholders.
- Origo evaluates persisted event details and fingerprints independently of the simulator's fixture checker. Legacy evidence without event-level detail remains inconclusive.
- Server reports are scoped to the selected user's workspace and disclose missing verification records and limitations.
- Sample/demo records are never treated as persisted API data or Origo verification.

See `../docs/stage4/01_API_AND_ORIGO_CONTRACTS.md` for contract details.
