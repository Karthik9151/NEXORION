# Stage 4 — UI/UX Implementation

## Scope delivered in this branch

The initial React + TypeScript + Vite frontend establishes the NEXORION workspace experience and implements six responsive interface areas: Mission Center, Digital World Explorer, Simulation Lab, Evidence & Origo Verification, Mission Reports, and Workspace Settings.

### Visual system

- Obsidian Gold is the default theme: dark graphite surfaces, restrained gold accenting, editorial headings, and fine panel separators.
- Polar Minimalist uses the same information architecture and layout hierarchy with white surfaces, slate dividers, technical orange accents, and sans-serif headings.
- A persistent ENV: SYNTHETIC (ISOLATED) banner appears throughout the authenticated and sample workspace.
- Shared components include lifecycle and verification tags, metrics, data tables, scope callouts, readiness checks, empty states, connection notices, and report exports.
- Responsive layouts collapse the sidebar and expose a bottom navigation bar on small screens. Touch controls remain visible and the graph canvas stays pannable/zoomable.
- Keyboard focus visibility and reduced-motion preferences are represented in the shared stylesheet.

### API integration

The frontend uses the existing FastAPI routes for authentication, missions, synthetic entities and relationships, baseline capture, and registered fixture runs. Workspace IDs and CSRF cookie tokens are supplied on requests where applicable. Vite proxies /api to the local API by default.

The backend currently supports these registered scenarios:
- scenario-auth-failure-v1
- scenario-auth-benign-control-v1

Other scenario cards are deliberately marked Planned rather than simulated with invented backend behavior.

Evidence and reports are based on evidence and run records returned by the API. Markdown and JSON reports are generated in the browser. The current verifier is a deterministic fixture-consistency checker; this branch does not claim to deliver the future full Origo verification engine.

### Sample mode

The interface provides an explicit sample environment to review the UI without an API session. Data and mutations in sample mode exist only in browser memory, carry an explicit sample notice, and are not sent to the backend.

### Local validation

From the frontend directory, install dependencies and run the production build:

    npm install
    npm run build

Backend behavior was left unchanged by this UI-only implementation. Cross-origin deployment still requires a backend CORS policy that allows the frontend origin with credentialed requests.


## Implementation handoff note

This document records the UI/UX-only source branch, \`stage4-ui-and-ux\`. The implementation branch \`stage4-implementation\` retains this interface and adds the server-side API contracts, persisted Origo verification and reports described in \`01_API_AND_ORIGO_CONTRACTS.md\`. For current backend behavior and verification status, use the implementation status document and backend README rather than treating this source-branch handoff as a description of final runtime behavior.
