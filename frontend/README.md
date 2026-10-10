# NEXORION Frontend

React + TypeScript + Vite interface for the NEXORION Synthetic Cyber Research Platform.

## Included workspaces

- Mission Center — workspace-scoped mission list, lifecycle overview, and synthetic mission creation.
- Digital World Explorer — interactive React Flow canvas for typed synthetic entities and relationships.
- Simulation Lab — registered authentication-failure and benign-control fixtures, with unregistered scenarios explicitly marked as planned.
- Evidence & Origo — evidence provenance, SHA-256 digests, and the current backend's bounded deterministic fixture checks.
- Mission Reports — browser-generated Markdown and JSON exports from run records.
- Settings — dual themes, session context, API connection status, and safety boundaries.

## Themes

The default Obsidian Gold theme uses dark surfaces and champagne/gold accents. Polar Minimalist switches the same architecture to white/slate surfaces and technical orange accents. The environment strip remains visible on every workspace page.

## Run locally

Requirements: Node.js 20+ and npm, plus the FastAPI backend.

    cd frontend
    npm install
    npm run dev

The Vite development server proxies /api/* to http://localhost:8000 by default. Override the proxy destination with NEXORION_API_ORIGIN, for example:

    NEXORION_API_ORIGIN=http://localhost:8000 npm run dev

The backend should be running on port 8000. Register or sign in to load workspace data. You can choose Explore sample environment to preview the interface without an API session; sample actions stay in browser memory and are labelled as sample data.

## Deployment configuration

For a deployed frontend, set VITE_API_BASE_URL to the backend API origin prefix, for example https://your-api.example.com. Since this frontend uses session and CSRF cookies, configure the backend to allow the deployed frontend origin with credentials and ensure production cookies are secure. Do not place secrets in VITE_ variables.

The project currently uses backend endpoints already present in the repository. Reports are generated in the browser from returned run records; there is no server-side reports endpoint in the current API.

## Security and interpretation boundaries

- Every mutation uses the backend's CSRF cookie value where available and the workspace header for workspace-scoped routes.
- Mission creation fixes scope to synthetic_only, excludes real systems/external networks, and requests the simulate_synthetic tier.
- The UI does not implement target scanning, shell execution, real credential handling, or live-system mutation.
- Only two simulation fixtures are executable by the current backend. Other scenario cards are roadmap placeholders.
- The API's verifier checks consistency against registered fixtures. The interface calls it bounded fixture verification, not a full independent Origo verifier.
- Sample/demo activity is never presented as persisted API data.
