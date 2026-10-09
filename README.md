# NEXORION

**An AI-coordinated cybersecurity research and simulation universe.**

NEXORION is a proposed persistent digital environment in which a researcher can explore a modeled world, investigate security evidence, develop hypotheses, run reproducible simulations, and independently verify findings. The concept combines a stateful world model, coordinated specialist roles, explicit governance, and a future isolated lab for separately authorized experiments.

> **Project status:** Research and architecture specification. The repository currently contains concept and planning documents; executable application source, runtime behavior, and security controls are not verified as implemented. Future capabilities described here are proposals, not existing features.

## The three identities

- **NEXORION — the digital universe:** the persistent environment and world model for entities, relationships, missions, scenarios, evidence, and research history.
- **NEXARCH — the central intelligence:** the primary mission reasoning and orchestration layer. It decomposes user intent into bounded work and coordinates specialists; it cannot authorize its own consequential actions.
- **ERGOUSIARCH — the governing authority:** the governance concept for policy, approval, audit, and execution-gate controls. It must be realized through deterministic software; the name itself is not an enforcement mechanism.

**Archon** is orchestration support under NEXARCH, not a competing primary orchestrator. **Origo** is the independent verification role. Other agent names and aliases in the source material are bounded role concepts, not a requirement to run a separate LLM for every name.

## Concept and distinguishing goals

- A persistent, inspectable digital world rather than a chat-only interface.
- Mission-based research with explicit objectives, scope, constraints, and completion criteria.
- Specialist roles with bounded responsibilities, typed handoffs, and prohibited authorities.
- Repeatable deterministic simulation and baseline comparison.
- Evidence provenance and independent verification separated from AI-generated hypotheses.
- An adaptive multimodal interface as a future direction, not a current capability claim.
- A staged path to an isolated lab only after separate security design, isolation validation, and explicit authorization.

## Proposed architecture

```mermaid
flowchart TB
    U[Researcher] --> UI[Interactive workspace]
    UI --> W[NEXORION: persistent world model]
    W --> N[NEXARCH: mission orchestration]
    N --> A[Bounded specialist roles and deterministic modules]
    N --> G[ERGOUSIARCH: policy, approval, and audit controls]
    A --> S[Deterministic synthetic simulation]
    S --> E[Evidence and mission record]
    E --> V[Origo: independent verification]
    V --> R[Findings, limitations, and report]
    G -. validates scope and authorization .-> S
    S -. future capability, separately isolated .-> L[Authorized lab, later phase]
```

This diagram represents the proposed design, not a verified implementation. The backend must remain authoritative for world state, permissions, and mission records; a UI graph or an agent's explanation is not a security boundary.

## Mission lifecycle

1. **Interpret intent:** capture the research question, assumptions, and constraints.
2. **Define scope:** create a versioned mission contract with permitted actions, exclusions, autonomy tier, and acceptance criteria.
3. **Validate and plan:** apply deterministic scope/policy checks and produce a bounded, versioned plan.
4. **Establish baseline:** capture the initial modeled state and evidence references.
5. **Execute within scope:** initially use deterministic synthetic fixtures only.
6. **Verify independently:** check provenance, expected outcomes, contradictions, and missing evidence.
7. **Report and retain:** record findings, limitations, linked evidence, and a reproducible mission outcome.

A blocked approval or unclear scope prevents execution. Failure, dispute, inconclusive evidence, or cancellation must never be reported as success.

## Stage 1 blueprint

Stage 1 is documentation-only: it defines requirements, contracts, lifecycle rules, security boundaries, technology decisions, a synthetic scenario, traceability, and owner decisions before application code is built.

- [Stage 1 index](docs/stage1/00_STAGE1_INDEX.md)
- [Requirements catalogue](docs/stage1/01_REQUIREMENTS_CATALOGUE.md)
- [Data and API contracts](docs/stage1/02_DATA_AND_API_CONTRACTS.md)
- [Mission lifecycle and recovery](docs/stage1/03_MISSION_LIFECYCLE.md)
- [Governance and security controls](docs/stage1/04_GOVERNANCE_SECURITY_CONTROLS.md)
- [Technology decision records](docs/stage1/05_TECHNOLOGY_DECISION_RECORDS.md)
- [Synthetic authentication-failure scenario](docs/stage1/06_SYNTHETIC_AUTH_FAILURE_SCENARIO.md)
- [Requirement-to-test traceability and acceptance](docs/stage1/07_REQUIREMENT_TO_TEST_TRACEABILITY.md)
- [Open owner decisions](docs/stage1/08_OPEN_DECISIONS.md)
- [Stage 1 delivery review](docs/stage1/09_STAGE1_DELIVERY_REVIEW.md)
- [Source-of-truth addendum](docs/stage1/10_SOURCE_OF_TRUTH_ADDENDUM.md)
- [Roadmap addendum](docs/stage1/11_ROADMAP_ADDENDUM.md)

Stage 1 is **proposed for owner review** until the requirements and acceptance checklist are explicitly accepted. These documents specify expected future behavior; they do not prove runtime, API, simulation, or security tests have passed.

## Core documentation

- [Concept and scope](docs/CONCEPT.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Agent registry](docs/AGENT_REGISTRY.md)
- [Mission coordination](docs/COORDINATION.md)
- [Governance and safety](docs/GOVERNANCE_AND_SAFETY.md)
- [Technology stack](docs/TECH_STACK.md)
- [Roadmap](docs/ROADMAP.md)
- [Threat model](docs/THREAT_MODEL.md)
- [Source of truth and open decisions](docs/SOURCE_OF_TRUTH.md)

## Original research and planning files

The original research files are preserved as foundational inputs. They may contain earlier role names, phase numbering, or architectural alternatives; conflicts are tracked instead of silently erasing the history.

- [AI Interactive Cybersecurity Architecture](AI_Interactive_Cybersecurity_Architecture.md)
- [Unified NEXORION concept and agent architecture](nexorion_unified_concept_agent_architecture.md)
- [Agent Identity, Responsibilities, and Coordination](Agent%20Identity%2C%20Responsibilities%2C%20and%20Coordination.md)
- [Hybrid cybersecurity lab simulation architecture](hybrid_cybersecurity_lab_simulation_architecture.md)
- [Hybrid implementation strategy roadmap](hybrid_implementation_strategy_roadmap.md)
- [Implementation notes](Implementation.md)
- [Project checklist](Checklist.md)

## Technology direction

The planning documents propose React + TypeScript + Vite for the workspace, React Flow for graph interaction, Python + FastAPI + Pydantic for an API boundary, PostgreSQL for durable metadata, NetworkX for early graph analysis, and WebSockets or Server-Sent Events where live updates are justified. Temporal is a candidate for durable workflows, not a committed dependency. Kafka/Redpanda, a dedicated graph database, 3D rendering, and a full agent framework are deferred until requirements demonstrate a need.

See [technology decision records](docs/stage1/05_TECHNOLOGY_DECISION_RECORDS.md). These are proposals, not a verified dependency manifest or deployed stack.

## Security principles

- Treat model/agent output as untrusted data, not authority.
- Enforce scope and permissions through deterministic checks at the execution boundary.
- Require explicit, narrow, time-bounded authorization where policy demands it; re-check before execution.
- Separate planning, approval, execution, and independent verification.
- Keep synthetic simulation distinct from user-supplied or observed evidence.
- Preserve evidence provenance and audit history; corrections create linked records.
- Fail closed when scope, approval, policy, or verifier status cannot be established.
- Never scan, test, or modify systems without explicit authorization.

## Development status and setup

The reviewed project materials are Markdown planning documents. Application source code, dependency manifests, verified test scripts, deployment configuration, and runtime behavior are not established by this blueprint. Therefore, no install, run, or test command is presented as verified. Those instructions should be added when implementation artifacts exist and the corresponding commands have been exercised.

## Roadmap

The intended sequence is: reconcile the blueprint; accept contracts and guardrails; implement the persistent world and mission foundation; build the synthetic authentication-failure vertical slice; add independent verification and evidence handling; introduce durable orchestration and bounded agent roles; then evaluate model-backed interaction and a separately isolated lab. Operational hardening and scaling should follow demonstrated requirements. See [roadmap](docs/ROADMAP.md) and [Stage 1 acceptance](docs/stage1/07_REQUIREMENT_TO_TEST_TRACEABILITY.md).

## Licensing and contributions

No license or contribution policy should be inferred from these documents. License choice, contribution workflow, support expectations, and a security vulnerability reporting channel remain owner decisions. Do not submit or run tests against systems without authorization.
