# Technology Stack and Decision Status

This document reconciles the technology direction recorded in the planning files. **A technology mentioned here is not thereby installed or implemented.** The supplied archive contains no source code or dependency manifests.

## Proposed implementation baseline

| Area | Direction in planning documents | Intended purpose | Status |
|---|---|---|---|
| Frontend | React + TypeScript + Vite | Interactive research workspace | Selected design direction; unverified |
| World visualization | React Flow | Interactive nodes, relationships, and workflow views | Initial visualization choice; unverified |
| Backend API | Python + FastAPI + Pydantic | API boundary, validation, typed contracts | Selected design direction; unverified |
| Primary persistence | PostgreSQL | Durable mission, world, evidence, and audit records | Selected design direction; unverified |
| Graph analysis | NetworkX | Initial in-process graph analysis | Initial choice; unverified |
| Live updates | WebSockets | Mission progress and event updates | Initial choice; unverified |
| Durable workflows | Temporal | Long-running mission state, retries, recovery | Planned integration; unverified |
| Specialist reasoning | Bounded agents and deterministic modules | Task-specific research and analysis | Architecture proposal |
| Simulation | Deterministic synthetic environment | Reproducible first mission | Planned |
| Lab isolation | Separately isolated environment, technology TBD | Authorized future experiments | Deferred, subject to safety gates |
| Observability | OpenTelemetry-compatible instrumentation is discussed in research | Traces, metrics, and logs | Proposed; unverified |

## Optional or deferred technologies

Cytoscape.js, Three.js, Kafka/Redpanda, dedicated graph storage, and additional distributed components should remain optional until concrete workload, visualization, throughput, or graph-query requirements justify them. Do not adopt multiple technologies that solve the same problem without an explicit reason.

The foundational research mentions LangGraph or a custom state machine as orchestration candidates. Later planning specifies Temporal for durable workflow orchestration. Treat this as an evolution in the design direction, not proof that the choice has been integrated. Clarify whether Temporal will own durable mission workflows while NEXARCH handles planning/coordination, and whether a separate agent framework is actually needed.

## Decision principles

- Prefer a small, testable vertical slice over building all infrastructure up front.
- Choose components based on acceptance criteria, operational capability, and total complexity.
- Keep policy enforcement and authorization deterministic even when AI proposes actions.
- Define data ownership, schema migration, backup, restore, and retention before relying on persistence.
- Define workflow idempotency, retries, cancellation, and recovery before long-running agent tasks.
- Measure actual need before adding event streaming, graph databases, 3D visualization, or distributed services.

## Missing operational decisions

The planning files do not establish verified production choices for cloud provider, deployment topology, secrets manager, identity provider, model provider, model data-retention terms, backup/restore objectives, availability targets, or cost limits. Record these as open decisions rather than inventing defaults.

## Evidence required to mark a technology implemented

A technology should be labelled implemented only after the repository contains the relevant code/configuration and the intended behavior is validated. Dependency declaration alone is not enough to claim an integration is working.
