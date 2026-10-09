# Source of Truth and Open Decisions

## Purpose

The repository contains multiple evolving planning documents. This map explains how to read them without silently overwriting original research or mistaking proposals for implementation.

## Recommended authority by subject

| Subject | Primary reference | Supporting source / caveat |
|---|---|---|
| Foundational research idea and initial requirements | `../AI_Interactive_Cybersecurity_Architecture.md` | Original conceptual requirements; retains candidate options |
| Three identities and full agent model | `../nexorion_unified_concept_agent_architecture.md` | Use as the proposed canonical naming hierarchy unless the project owner decides otherwise |
| Short-form agent definitions | `../Agent Identity, Responsibilities, and Coordination.md` | Conflicts by calling Archon the primary coordinator; preserve as source and reconcile explicitly |
| Hybrid component architecture and lab boundary | `../hybrid_cybersecurity_lab_simulation_architecture.md` | Design proposal, not implementation evidence |
| Implementation sequencing and acceptance gates | `../hybrid_implementation_strategy_roadmap.md` | Shares intent with other plans but uses a different phase structure |
| Detailed implementation prompt | `../Implementation.md` | Planning/instruction document, not evidence of completed code |
| Readiness checklist | `../Checklist.md` | Unchecked items are not complete; checkmarks require evidence |

## Reconciliation decisions used in the maintained docs

1. NEXORION means the persistent digital universe/world model.
2. NEXARCH means central intelligence and mission orchestration.
3. ERGOUSIARCH means the governing-authority concept, implemented through enforceable services rather than an agent's self-declared authority.
4. Archon is treated as orchestration support, not as a second central orchestrator.
5. Alias groups remain single roles: Aleph/Alpha; Genesis/Genarch; Primus/Prime/Prior.
6. The hybrid architecture is the current planning direction.
7. A deterministic synthetic authentication-failure investigation is the first proposed vertical slice.
8. Isolated lab execution is deferred until governance, authorization, verification, isolation, and cleanup gates are testable.
9. The canonical roadmap in `ROADMAP.md` groups shared phases into one sequence. Original phase numbering remains unchanged in source documents.
10. Technology references describe planning choices; none are labelled implemented without code evidence.

These are documentation reconciliation choices made to remove ambiguity. The project owner should confirm them before implementation relies on them.

## Open decisions requiring owner confirmation

- Is the unified concept definitively authoritative for agent hierarchy and naming?
- Should the earlier agent document be updated in a later approved pass to remove the Archon/NEXARCH contradiction, or retained indefinitely as historical source?
- Is Temporal the final durable workflow engine, and is any separate agent framework required?
- What exact scope does ERGOUSIARCH own in software: policy definition, policy decision service, approval workflow, audit, or all of these through separate modules?
- What autonomy tier is allowed by default, and what actions always require explicit approval?
- What are the initial deployment model, identity provider, model provider, data retention terms, and cost limits?
- What metrics define successful verification, reproducibility, and operational readiness?
- What licence, contribution policy, and vulnerability-reporting channel should be adopted? No licence is added by this documentation change.

## Evidence standard

A claim may be described as implemented only when source code/configuration exists and the intended behavior has been verified. A checklist, architecture diagram, dependency suggestion, or roadmap item alone is not implementation evidence.


## Stage 1 blueprint detail package

The Stage 1 detail package in `docs/stage1/` expands the blueprint into testable requirements and contracts. It supplements rather than replaces the original concept documents.

| Topic | Stage 1 detail |
|---|---|
| Requirements and dependencies | [`01_REQUIREMENTS_CATALOGUE.md`](stage1/01_REQUIREMENTS_CATALOGUE.md) |
| Data and proposed API contracts | [`02_DATA_AND_API_CONTRACTS.md`](stage1/02_DATA_AND_API_CONTRACTS.md) |
| Mission states, transitions and recovery | [`03_MISSION_LIFECYCLE.md`](stage1/03_MISSION_LIFECYCLE.md) |
| Governance and security controls | [`04_GOVERNANCE_SECURITY_CONTROLS.md`](stage1/04_GOVERNANCE_SECURITY_CONTROLS.md) |
| Technology decision records | [`05_TECHNOLOGY_DECISION_RECORDS.md`](stage1/05_TECHNOLOGY_DECISION_RECORDS.md) |
| First synthetic vertical slice | [`06_SYNTHETIC_AUTH_FAILURE_SCENARIO.md`](stage1/06_SYNTHETIC_AUTH_FAILURE_SCENARIO.md) |
| Requirement-to-test traceability and acceptance | [`07_REQUIREMENT_TO_TEST_TRACEABILITY.md`](stage1/07_REQUIREMENT_TO_TEST_TRACEABILITY.md) |
| Owner decisions that remain open | [`08_OPEN_DECISIONS.md`](stage1/08_OPEN_DECISIONS.md) |
| Stage 1 scope and status review | [`09_STAGE1_DELIVERY_REVIEW.md`](stage1/09_STAGE1_DELIVERY_REVIEW.md) |

**Authority rule:** these files specify the proposed implementation contract for Stage 1 planning. They do not establish that an API, database schema, agent, policy gate, workflow runner, scenario engine, or security control is implemented or tested. If a conflict with an original source is found, preserve the original and record an owner decision in the open-decision log rather than silently deleting historical research.
