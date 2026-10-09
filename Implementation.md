# Master Implementation Prompt — AI Interactive Cybersecurity Research and Simulation Environment

## 1. Project objective

Act as a senior software architect, cybersecurity engineer, AI systems engineer, and full-stack developer. Help me implement the system described in `AI_Interactive_Cybersecurity_Architecture.md`.

Build a **persistent, interactive digital cybersecurity research and simulation environment**, not merely a chatbot or a conventional security dashboard.

The central experience must be a digital world that I can explore, inspect, simulate, investigate, modify within authorized boundaries, and use to understand cybersecurity scenarios. The AI should interact with me through an adaptive interface, help formulate hypotheses, conduct bounded research, propose experiments, interpret evidence, and explain verified outcomes.

Treat the architecture document as the primary source of truth. Do not silently remove requirements, invent existing functionality, or replace the technology decisions already finalized.

## 2. Finalized technology stack

Use the following baseline:

- **Frontend:** React + TypeScript + Vite.
- **2D digital-world visualization:** React Flow.
- **Advanced graph exploration:** Cytoscape.js when graph size or interaction requirements justify it.
- **Optional 3D environment:** Three.js, introduced only when it provides meaningful value.
- **Backend and API:** Python + FastAPI + Pydantic.
- **Durable mission orchestration:** Temporal, including the required Temporal service, workflows, and workers.
- **Real-time updates:** WebSockets initially; Kafka or Redpanda only when demonstrated event throughput or distribution requirements justify them.
- **Primary database:** PostgreSQL.
- **Initial graph analysis:** NetworkX.
- **Graph storage:** Start with PostgreSQL and NetworkX. Introduce a dedicated graph database only if measured requirements justify it.
- **Testing:** Unit, integration, API-contract, workflow-recovery, frontend, security, and end-to-end tests appropriate to each implementation phase.
- **Development and operations:** Reproducible local setup, configuration through environment variables, database migrations, structured logs, health checks, and documented startup and testing procedures.

Do not substitute the finalized technologies without explaining the specific requirement that cannot be met.

## 3. Required architectural behavior

Design and implement the system around this lifecycle:

User intent → digital-world model and evidence → AI reasoning and planning → independent policy checks → authorized simulation or action → independent verification → updated world state and mission record.

Enforce these principles:

1. The digital simulation environment is the primary interface and organizing model.
2. Separate AI planning, policy authorization, execution, and verification.
3. The AI cannot grant itself permissions or bypass approval requirements.
4. Every mission must have a defined objective, scope, constraints, status, evidence, and outcome.
5. Distinguish `observed`, `inferred`, `hypothesized`, `simulated`, `unknown`, and `stale` information.
6. Never represent simulated results as observations of a real environment.
7. Require explicit authorization and human approval for consequential actions.
8. Make long-running missions recoverable after failures and restarts.
9. Record important actions, decisions, evidence, approvals, and verification results in an auditable history.
10. Show uncertainty and verification status rather than presenting AI-generated claims as established facts.
11. Make the interface adaptive and interactive without allowing interface convenience to bypass security controls.
12. Keep the initial implementation small enough to test completely, while preserving a path to a scalable architecture.

## 4. First implementation milestone

Start with a deterministic **simulated authentication-failure investigation**.

Represent a fictional web application, authentication service, and database in the digital world.

Implement these capabilities:

- Create and inspect a mission.
- Display the fictional system and its dependencies using React Flow.
- Retrieve synthetic authentication logs and evidence through FastAPI.
- Store mission metadata, evidence references, findings, and results in PostgreSQL.
- Use Pydantic schemas to validate API requests and responses.
- Use NetworkX for basic dependency and path analysis.
- Simulate a documented authentication configuration failure using deterministic Python logic.
- Run a separate verifier that checks the simulated outcome against explicit expected conditions.
- Show the mission lifecycle and execution progress in the frontend.
- Send meaningful status updates through WebSockets.
- Persist the mission state so the investigation can be resumed after a restart.
- Provide an audit trail and a clear explanation of what the system did and did not verify.
- Add automated tests for expected success, expected failure, invalid inputs, unauthorized actions, and verification failures.

Keep this milestone fully simulated. Do not connect to real targets, perform real exploitation, or execute unreviewed commands on external systems.

## 5. Implementation sequence

Implement one phase at a time:

**Phase 0 — Architecture and repository inspection**

- Read `AI_Interactive_Cybersecurity_Architecture.md` completely.
- Inspect the current workspace and existing files before creating or modifying anything.
- Map requirements to components, interfaces, data models, and tests.
- Identify conflicts, ambiguities, dependencies, and missing decisions.
- Produce a requirements traceability checklist.
- Do not create a repository, deploy services, or modify files until I explicitly authorize implementation.

**Phase 1 — Foundation**

- Establish the frontend and backend structure.
- Add configuration and dependency management.
- Define typed API contracts and the initial database schema.
- Provide reproducible local development instructions.

**Phase 2 — Interactive digital world**

- Build the world view, asset/dependency nodes, edges, and inspection panel.
- Add a minimal mission creation and selection experience.
- Load world data from the backend instead of hardcoding the entire experience in the frontend.

**Phase 3 — Simulation and evidence**

- Implement synthetic evidence and deterministic simulation.
- Add NetworkX analysis and structured findings.
- Keep evidence provenance and information-state labels visible.

**Phase 4 — Verification and persistence**

- Add an independent verifier with explicit assertions.
- Persist mission state, evidence metadata, events, and results.
- Test database failures, verification failures, and restart recovery.

**Phase 5 — Durable orchestration and live interaction**

- Integrate Temporal workflows and workers.
- Implement WebSocket progress updates.
- Define retry, timeout, cancellation, idempotency, and recovery behavior.

**Phase 6 — Security and authorization**

- Implement authentication and authorization where required.
- Enforce mission scope, action permissions, approval gates, execution limits, and audit logging.
- Test attempts to bypass policy and unauthorized mission access.

**Phase 7 — AI integration**

- Add AI-assisted hypothesis generation, planning, evidence interpretation, and explanations.
- Treat model output as untrusted input.
- Validate proposed actions using deterministic schemas and independent policy checks.
- Do not allow the model to directly bypass the execution and verification layers.

**Phase 8 — Advanced capabilities**

- Consider Cytoscape.js, Three.js, Kafka/Redpanda, specialized graph storage, and isolated lab infrastructure only when measurable needs justify them.
- Add controlled lab execution, research-source ingestion, branching investigations, and richer multimodal interaction in separately testable increments.

## 6. Engineering requirements

- Use clear module boundaries and maintainable naming.
- Use typed contracts and explicit validation.
- Keep secrets out of source code and frontend bundles.
- Include dependency locking or reproducible dependency specifications.
- Add database migrations rather than relying on ad hoc schema changes.
- Use structured error responses and meaningful request/task identifiers.
- Add unit and integration tests alongside implementation.
- Make background work observable and recoverable.
- Use idempotency for retryable operations where appropriate.
- Log enough information for diagnosis without unnecessarily exposing sensitive data.
- Document assumptions, limitations, threat models, and operational dependencies.
- Avoid placeholder implementations that appear functional but do not perform the advertised behavior.
- Do not claim a feature is complete until its acceptance tests pass.
- Do not introduce unnecessary infrastructure or dependencies.

## 7. Required deliverables for every phase

For each phase, provide:

1. Requirements addressed and their source sections.
2. Architecture and design decisions.
3. Files to be created or changed.
4. Implementation details and dependencies.
5. Database and API changes, if any.
6. Security and failure-handling considerations.
7. Automated tests and exact commands to run.
8. Test results, including failures and limitations.
9. Acceptance criteria with pass/fail status.
10. Documentation updates and the next recommended phase.

Maintain a requirements-to-code-to-test traceability table throughout development.

## 8. Definition of done

A phase is complete only when its agreed acceptance criteria are implemented, its tests have been run, results are reported truthfully, and its documentation is updated.

The initial milestone must demonstrate a complete simulated investigation from mission creation through world inspection, evidence collection, deterministic simulation, independent verification, persisted results, and visible mission completion.

Do not claim production readiness solely because a local prototype works. Document the remaining security, reliability, scaling, deployment, and operational work separately.

## 9. Working protocol

Begin by reading `AI_Interactive_Cybersecurity_Architecture.md` and presenting:

- A concise understanding of the system.
- The finalized technology matrix.
- A requirements checklist grouped by architecture section.
- The proposed repository structure.
- The first milestone's scope and acceptance tests.
- Missing decisions, risks, and dependencies.
- A phased implementation plan.

**Stop after the planning and review stage. Do not modify code or files, create a GitHub repository, deploy anything, provision infrastructure, or incur costs until I explicitly say: `IMPLEMENT PHASE 1`.**

When implementation is authorized, work only on the approved phase, show the planned file changes, run available tests, report actual results, and wait for approval before advancing to the next phase.