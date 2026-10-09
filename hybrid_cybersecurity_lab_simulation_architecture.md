# Hybrid Architecture --- AI Cybersecurity Research, Simulation, and Lab Platform

## 1. Architecture Decision

**Selected architecture: Hybrid**

The platform will combine a modular application backend, coordinated
AI-agent roles, durable mission workflows, an interactive digital-world
model, deterministic simulation, and a separately controlled execution
boundary for future isolated cybersecurity labs.

The hybrid design is intended to support a realistic, extensible
platform without prematurely splitting every component into a
microservice. It keeps the first implementation manageable while
preserving clear boundaries for scale, security, and future lab
execution.

## 2. Selected Design Choices

  -----------------------------------------------------------------------
  Decision area           Selection               Rationale
  ----------------------- ----------------------- -----------------------
  Overall architecture    **Hybrid**              Combines modular
                                                  backend services, agent
                                                  roles, durable
                                                  workflows, and a
                                                  separate lab boundary.

  Initial execution       **Containerized local   Supports reproducible
                          development**           development and testing
                                                  without requiring
                                                  deployment.

  Agent architecture      **Hybrid: typed modules Establishes reliable
                          first, model-backed     contracts and
                          agents gradually**      deterministic behavior
                                                  before introducing
                                                  autonomous model-driven
                                                  roles.

  Lab strategy            **Design the isolation  Makes containment and
                          boundary now; implement authorization part of
                          the lab later**         the architecture from
                                                  the beginning without
                                                  making the first
                                                  milestone depend on a
                                                  full cyber range.

  Primary interaction     Adaptive, multimodal    Makes the digital
                          research workspace      simulation environment
                                                  the central interface
                                                  rather than treating
                                                  the system as a
                                                  chat-only assistant.

  World visualization     React Flow initially;   Supports an interactive
                          Cytoscape.js if graph   asset and dependency
                          scale demands it        graph, with a path to
                                                  more complex graph
                                                  exploration.

  Optional 3D view        Three.js, when          Adds an immersive world
                          justified               view without making 3D
                                                  a requirement for the
                                                  first milestone.
  -----------------------------------------------------------------------

## 3. High-Level Architecture Chart

``` mermaid
flowchart TD
    USER[Researcher / User]
    UI[Interactive Research Workspace<br/>React + TypeScript + Vite]
    WORLD[Digital World Model<br/>Assets, Services, Dependencies, State]
    API[Typed API and Control Plane<br/>FastAPI + Pydantic]
    MISSION[Mission Manager]
    TEMPORAL[Durable Workflow Orchestration<br/>Temporal Service + Workers]
    AGENTS[Agent Coordination Layer]
    ARCHON[Archon — Chief Orchestrator]
    ALEPH[Aleph — World Intelligence]
    MNEME[Mneme — Intelligence and Memory]
    MELETE[Melete — Research Strategist]
    PROTOS[Protos — Simulation Engineer]
    POLICY[Kratos — Policy and Control]
    AUTH[Exousia — Authorization Gateway]
    SIM[Deterministic Simulation Engine]
    LAB[Isolated Lab Execution Boundary<br/>Future capability]
    VERIFY[Origo — Independent Verifier]
    DB[(PostgreSQL)]
    GRAPH[Graph Analysis<br/>NetworkX initially]
    EVENTS[Live Event Updates<br/>WebSockets initially]
    BUS[Kafka / Redpanda<br/>Only if throughput requires it]

    USER --> UI
    UI <--> API
    API <--> WORLD
    API --> MISSION
    MISSION <--> TEMPORAL
    TEMPORAL --> AGENTS
    AGENTS --> ARCHON
    ARCHON --> ALEPH
    ARCHON --> MNEME
    ARCHON --> MELETE
    ARCHON --> PROTOS
    ALEPH <--> WORLD
    ALEPH <--> GRAPH
    MNEME <--> DB
    MELETE --> SIM
    PROTOS --> SIM
    PROTOS -. approved future execution only .-> LAB
    SIM --> VERIFY
    LAB --> VERIFY
    POLICY --> AUTH
    AUTH --> SIM
    AUTH -. separate approval and scope checks .-> LAB
    VERIFY --> WORLD
    WORLD <--> DB
    MISSION <--> DB
    API --> EVENTS
    EVENTS --> UI
    EVENTS -. scale-driven replacement/extension .-> BUS
```

**Important:** Agent names represent proposed responsibilities, not
implemented agents. The diagram describes the intended architecture, not
an existing or deployed system.

## 4. Main Architectural Layers

### A. Interactive experience layer

-   **React + TypeScript + Vite:** primary user interface.
-   **React Flow:** initial interactive map of assets, services,
    dependencies, missions, and findings.
-   **Cytoscape.js:** optional upgrade when graph size or graph-analysis
    interactions require it.
-   **Three.js:** optional immersive 3D representation.
-   **WebSockets:** live mission status, simulation events, and evidence
    updates.

### B. API and control plane

-   **Python + FastAPI + Pydantic:** typed API endpoints, input
    validation, mission commands, and response schemas.
-   Authentication, authorization, request validation, audit records,
    and policy checks belong in explicit backend modules.
-   The API must not give an AI model unrestricted access to the host or
    lab environment.

### C. Digital world model

Represent the environment as structured entities and relationships, such
as:

-   Hosts, applications, services, identities, databases, and network
    segments.
-   Dependencies and trust relationships.
-   Configuration state and observed behavior.
-   Evidence, findings, hypotheses, and mission links.
-   Timestamps, provenance, confidence, and freshness.

Label information clearly as **observed, inferred, hypothesized,
simulated, unknown, or stale**. Do not present a simulation result as a
real-world observation.

### D. Mission orchestration

-   **Temporal:** durable, recoverable long-running workflows.
-   **Temporal Service and worker processes:** required parts of a
    running Temporal deployment; Temporal is not merely a Python library
    import.
-   Persist mission state and workflow outcomes so a process restart
    does not silently erase progress.
-   Support retries, timeouts, cancellation, approvals, and recovery.

### E. Agent coordination

Begin with well-defined software modules and typed interfaces. Introduce
model-backed agents incrementally where they provide measurable value.

  -----------------------------------------------------------------------
  Proposed role           Responsibility          Boundary
  ----------------------- ----------------------- -----------------------
  **Archon**              Coordinates missions    Does not independently
                          and specialist roles    authorize consequential
                                                  actions.

  **Aleph**               Maintains and queries   Must preserve
                          the digital world model provenance and
                                                  uncertainty.

  **Mneme**               Retrieves mission       Must respect access
                          history and relevant    controls and
                          evidence                data-retention rules.

  **Melete**              Develops hypotheses and Plans are proposals,
                          experiment plans        not permissions.

  **Protos**              Builds and runs         Executes only within
                          deterministic           the approved scope.
                          simulations             

  **Kratos**              Applies predefined      Policy decisions should
                          policy and execution    be explicit and
                          constraints             testable.

  **Exousia**             Checks approval         Must not create its own
                          records, scope, and     authority or treat
                          action permissions      model confidence as
                                                  approval.

  **Origo**               Independently verifies  Should not merely
                          outputs against         repeat the executor's
                          assertions and evidence claim of success.
  -----------------------------------------------------------------------

Agents should communicate through typed contracts and durable mission
events rather than receiving unrestricted access to every tool.

### F. Simulation and lab execution

Keep these execution modes distinct:

1.  **Model-based simulation:** deterministic, synthetic scenarios and
    state transitions.
2.  **Isolated virtual lab:** a later capability for controlled
    experiments inside a separately contained environment.
3.  **Observed authorized environment:** a future integration mode
    limited to explicitly authorized assets and actions.

The first milestone should use deterministic simulation. Design the lab
boundary now, but do not implement real lab execution until isolation,
scope enforcement, approval, logging, resource limits, and cleanup can
be tested.

### G. Independent verification

The verifier should check explicit expected outcomes, invariants, and
evidence. It should be separate from the component that performs the
simulation or lab action.

Example checks: - Did the simulated authentication failure occur under
the specified conditions? - Did the proposed configuration fix change
the expected outcome? - Were all actions within the approved scenario? -
Do the recorded evidence and final mission status agree?

### H. Data and graph analysis

-   **PostgreSQL:** primary durable store for missions, world entities,
    evidence metadata, approvals, workflow state references, and audit
    records.
-   **NetworkX:** initial in-process graph analysis for dependencies and
    paths.
-   Add a dedicated graph database only if measured query scale or graph
    workloads justify it.
-   Add vector search only when semantic retrieval needs are
    established; it is not a mandatory first-milestone dependency.

### I. Event distribution and scale

-   Start with **WebSockets** for live UI updates.
-   Introduce **Kafka or Redpanda** only when event volume, fan-out,
    replay, or service-decoupling requirements justify the operational
    cost.
-   Do not add a message broker merely because the architecture may
    eventually scale.

## 5. First End-to-End Scenario

**Scenario: simulated authentication-failure investigation**

1.  The user opens a fictional environment in the interactive workspace.
2.  The digital world shows a web application, authentication service,
    and database.
3.  FastAPI provides synthetic logs and scenario metadata.
4.  The user starts a mission to investigate repeated authentication
    failures.
5.  Archon coordinates world inspection, evidence retrieval, and
    hypothesis generation.
6.  Melete proposes a testable explanation and a simulation plan.
7.  Kratos checks the policy; Exousia confirms the action is within the
    allowed simulation scope.
8.  Protos runs a deterministic simulation.
9.  Origo checks the results against explicit assertions.
10. PostgreSQL stores mission and evidence metadata; Temporal preserves
    workflow progress.
11. WebSockets update the interface with mission progress, findings, and
    verification status.
12. The user can inspect the evidence, compare before/after states, and
    resume the mission.

No real system should be scanned or modified in this first scenario.

## 6. Proposed Repository Structure

``` text
ai-cyber-research/
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── world/
│       │   ├── missions/
│       │   ├── evidence/
│       │   └── agents/
│       ├── pages/
│       ├── api/
│       └── types/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── world/
│   │   ├── graph/
│   │   ├── simulation/
│   │   ├── verification/
│   │   ├── policy/
│   │   └── agents/
│   ├── migrations/
│   └── tests/
├── workflows/
│   ├── missions/
│   └── workers/
├── infrastructure/
│   └── local-development/
├── docs/
│   ├── AI_Interactive_Cybersecurity_Architecture.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── REQUIREMENTS_TRACEABILITY.md
│   └── SECURITY_MODEL.md
└── README.md
```

This is a proposed structure for future implementation, not a claim that
these files already exist.

## 7. Phased Implementation Roadmap

### Phase 0 --- Architecture and requirements

-   Confirm requirements, trust boundaries, data classifications, and
    acceptance criteria.
-   Record the chosen stack and architecture decisions.
-   Define what the first milestone will and will not do.

### Phase 1 --- Application foundation

-   Set up the React/TypeScript frontend and FastAPI backend.
-   Define typed API contracts, configuration handling, database
    migrations, and automated tests.
-   Run locally in a reproducible containerized development setup.

### Phase 2 --- Digital world model

-   Define world entities, relationships, state, provenance, and
    evidence labels.
-   Render the world in React Flow.
-   Add initial NetworkX graph queries.

### Phase 3 --- Deterministic simulation and verification

-   Build the fictional authentication-failure scenario.
-   Define expected results and invariants.
-   Add independent verification and persist evidence.

### Phase 4 --- Durable missions and live updates

-   Integrate PostgreSQL-backed mission records.
-   Add Temporal workflows and worker processes.
-   Publish mission progress to the UI over WebSockets.
-   Test cancellation, retry, and restart recovery.

### Phase 5 --- Agent coordination

-   Implement typed role interfaces and bounded responsibilities.
-   Add Archon, Aleph, Mneme, Melete, Protos, Kratos, Exousia, and Origo
    as modules first.
-   Test policy enforcement and independent verification.

### Phase 6 --- Model-backed reasoning and adaptive interaction

-   Add model-backed planning or specialist behavior where justified.
-   Keep plans separate from permissions and execution.
-   Display uncertainty, provenance, and simulation-versus-reality
    status.

### Phase 7 --- Isolated lab capability

-   Implement only after the isolation boundary, approval flow, resource
    limits, audit trail, and cleanup behavior are testable.
-   Use explicitly authorized lab assets and scoped experiments.
-   Do not permit unrestricted host access or unapproved external
    actions.

### Phase 8 --- Scale-driven capabilities

-   Consider Cytoscape.js, Three.js, Kafka/Redpanda, or specialized
    storage only when requirements and measurements justify them.
-   Add operational monitoring, backup/recovery tests, performance
    testing, and security reviews.

## 8. Core Safety and Reliability Requirements

-   Separate planning, authorization, execution, and verification.
-   AI-generated content is untrusted input until validated.
-   Every consequential action must be scoped and authorized
    independently of the model.
-   Record approvals, action parameters, results, timestamps, and
    responsible components.
-   Enforce timeouts, rate limits, resource budgets, cancellation, and
    cleanup.
-   Protect secrets and credentials; never expose backend secrets to the
    frontend.
-   Treat external documents, logs, and threat-intelligence content as
    data, not executable instructions.
-   Show failures and uncertainty honestly; do not invent progress or
    claim unverified success.
-   Keep simulated results clearly distinguishable from observed
    real-world evidence.
-   Test policy bypasses, malformed inputs, workflow interruption,
    replay, and verification failures.

## 9. Initial Definition of Done

The first milestone is complete only when:

-   The user can view and interact with the fictional environment graph.
-   A mission can be started and its state is persisted.
-   Synthetic evidence can be inspected with provenance.
-   The deterministic simulation produces repeatable outcomes.
-   The independent verifier detects both expected success and
    intentionally introduced failures.
-   The UI receives real mission updates over WebSockets.
-   Mission state survives an application or worker restart.
-   Scope and policy checks block disallowed simulation actions.
-   Automated tests cover the core workflow and failure paths.
-   Documentation clearly states what is simulated and what is not
    implemented.

## 10. Decisions to Revisit Later

Revisit these only when evidence or requirements justify a change:

-   Whether graph complexity requires Cytoscape.js.
-   Whether a 3D world materially improves the workflow enough to
    justify Three.js.
-   Whether event volume requires Kafka or Redpanda.
-   Whether semantic retrieval justifies vector search.
-   Whether a dedicated graph database is needed.
-   Which model providers or locally hosted models meet quality,
    latency, privacy, and cost requirements.
-   Which virtualization or sandbox technology can enforce the future
    lab's isolation requirements.

## 11. Current Status

**Architecture decision recorded: Hybrid.**

This document is a planning artifact. It does not create a repository,
modify code, deploy services, provision infrastructure, or claim that
any component is implemented. Begin implementation only after the user
explicitly authorizes it.
