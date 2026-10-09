# Threat Model

**Status:** Preliminary design-level threat model. This is not a security assessment of an implemented system.

## Assets to protect

- User identities, workspace boundaries, and authorization decisions.
- Mission contracts, target scope, and approval records.
- World-model state, baselines, scenarios, and mission history.
- Evidence integrity, provenance, and verification results.
- Model/provider credentials, lab credentials, and other secrets.
- Simulation and lab workloads, networks, artifacts, and host resources.
- Audit logs, operational telemetry, and sensitive research data.

## Trust boundaries

1. User input to the application/API.
2. Workspace and tenant boundaries.
3. NEXARCH to specialist agents and tools.
4. Model-generated content to deterministic execution.
5. Synthetic simulation data to evidence presented as observation.
6. Application control plane to future lab execution.
7. Hypothesis generation to independent verification.
8. External model, package, or service providers to platform data.

## Threats and required mitigations

| Threat | Potential impact | Required mitigation / verification |
|---|---|---|
| Prompt injection in mission content or evidence | Agent follows untrusted instructions or leaks data | Treat content as data, separate instructions from evidence, restrict tools, test adversarial fixtures |
| Agent exceeds mission scope | Unauthorized or unintended action | Enforce allowlists and scope at the execution boundary; denial tests |
| Forged, stale, or overbroad approval | Consequential action without valid consent | Bind approvals to principal, action, target, scope, expiry, and policy version |
| Cross-workspace access | Disclosure or modification of another user's data | Server-side authorization on every resource operation; isolation tests |
| Fabricated or misattributed evidence | False findings and unsafe decisions | Provenance metadata, immutable/run-linked records where feasible, independent verification |
| Simulation presented as real observation | Misleading conclusions | Typed evidence origin and prominent mode labels in records and reports |
| Tool output or file content contains hostile payloads | Parser/UI compromise or downstream injection | Validate schemas, sanitize rendering, restrict file handling and tool capabilities |
| Lab escape or unintended network egress | Harm to host or external systems | Strong isolation, egress controls, least privilege, disposable workloads, stop/cleanup tests |
| Secret exposure in prompts/logs | Credential compromise | Secret references rather than values, redaction, access control, rotation, log review |
| Workflow retry duplicates an action | Repeated or harmful operation | Idempotency keys, explicit action semantics, bounded retries, reconciliation |
| Verifier shares the same faulty assumption | Incorrect result marked verified | Independent method/oracle, negative tests, record discrepancies |
| Resource exhaustion or runaway agents | Availability and cost impact | Budgets, timeouts, concurrency limits, cancellation, quotas and monitoring |
| Supply-chain compromise | Malicious dependencies or build artifacts | Dependency review, lockfiles, vulnerability scanning, reproducible build practices as applicable |

## Risk prioritization

Before implementation, rank threats using the actual deployment model, data sensitivity, agent tool access, and lab design. This document does not assign numeric risk scores because those facts are not established in the supplied archive.

## Open questions

- Will the initial release be local-only, hosted, or both?
- What user/workspace identity and authorization model is required?
- Which data may be sent to an external model provider, and under what retention terms?
- What are the lab isolation technology, network egress policy, and emergency stop mechanism?
- What audit retention and evidence integrity guarantees are required?
- What is the process for reporting and responding to vulnerabilities?

## Validation requirement

Each mitigation must map to a test, review, or operational control. A threat-model entry is not proof that a mitigation exists.
