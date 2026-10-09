# Agent Registry

**Status:** Proposed roles and aliases. These are not evidence of implemented agents.

## Organizational boundaries

- **NEXORION** is the world and persistent environment, not another specialist agent.
- **NEXARCH** is the central intelligence and mission orchestrator.
- **ERGOUSIARCH** is the governing-authority concept; enforcement must be implemented by deterministic services.
- Specialist agents contribute bounded capabilities. Deterministic modules perform validation, state changes, policy checks, and reproducible computation where appropriate.

## Registry

| Name | Alias(es) | Proposed responsibility | Boundary / output |
|---|---|---|---|
| NEXARCH | — | Mission orchestration and coordination | Mission plan, task assignments, consolidated result; cannot self-authorize |
| Monarque | — | User-intent interpretation | Clarified objective, assumptions, unresolved questions |
| Archon | — | Orchestration support | Dependency tracking, delegation support, coordination status; subordinate to NEXARCH |
| Dynas | — | Resource management | Resource estimates, quotas, capacity and scheduling recommendations |
| Kratos | — | Policy enforcement | Policy decision through deterministic, auditable controls; not an unconstrained LLM judgment |
| Exousia | — | Approval validation | Checks approval identity, scope, expiry, and action binding |
| Prytanie | — | Governance operations | Governance records, review workflow, policy lifecycle support |
| Aleph | Alpha | World intelligence | Entity/relationship interpretation and world-state summaries |
| Genesis | Genarch | Scenario creation | Scenario specification, preconditions, expected outcomes and cleanup plan |
| Primus | Prime, Prior | Priority arbitration | Ranked mission/task candidates with explicit rationale and constraints |
| Ab-Initio | — | Baseline establishment | Initial-state snapshot and baseline completeness report |
| Origo | — | Independent verification | Verification result, evidence references, discrepancies and limitations |
| Mneme | — | Evidence memory | Evidence indexing, retrieval and provenance references; does not invent missing evidence |
| Melete | — | Research strategy | Research plan, hypotheses, alternatives, and information gaps |
| Arkeon | — | Environment stewardship | Environment lifecycle, state consistency, reset and cleanup coordination |
| Protos | — | Simulation execution | Bounded simulation run, execution trace, outputs and run metadata |

## Aliases and consolidation policy

Aliases represent naming variants for the same proposed role unless a future approved specification explicitly separates them. Do not create duplicate agents for Aleph/Alpha, Genesis/Genarch, or Primus/Prime/Prior.

## Role overlaps to preserve and clarify

- **NEXARCH and Archon:** central authority versus orchestration support. The unified concept's hierarchy is the proposed canonical interpretation.
- **ERGOUSIARCH, Kratos, Exousia, and Prytanie:** governance identity, enforcement, approval validation, and governance operations are distinct responsibilities. They should not be collapsed into a single natural-language agent that can approve its own actions.
- **Ab-Initio and Origo:** baseline creation versus independent verification. Origo may consume a baseline but must not simply certify its own generated claim.
- **Aleph and NEXORION:** world intelligence interprets state; NEXORION owns the conceptual world/environment.
- **Genesis and Protos:** scenario definition versus execution.
- **Mneme and the world model:** evidence memory indexes evidence and provenance; it does not replace authoritative state or evidence storage.
- **Primus and Kratos:** priority is not permission. A high-priority task remains blocked if policy disallows it.

## Shared task contract

Every delegated task should define:
- Mission and task identifiers.
- Objective and permitted scope.
- Inputs and their provenance.
- Allowed tools and resource budget.
- Expected output schema.
- Deadline, cancellation, and retry behavior.
- Required evidence and validation checks.
- Escalation path for ambiguity, policy denial, or unexpected results.

## Minimum constraints

No specialist can widen mission scope, mint its own approval, bypass policy, or claim independent verification of its own output. Model-generated arguments must be validated before use. A failed or unavailable specialist must result in an explicit incomplete/blocked state, not fabricated completion.

The full source of role definitions is [`../nexorion_unified_concept_agent_architecture.md`](../nexorion_unified_concept_agent_architecture.md). The shorter [`../Agent Identity, Responsibilities, and Coordination.md`](../Agent%20Identity%2C%20Responsibilities%2C%20and%20Coordination.md) conflicts on the primary orchestrator and is preserved as historical source material pending an explicit source update.
