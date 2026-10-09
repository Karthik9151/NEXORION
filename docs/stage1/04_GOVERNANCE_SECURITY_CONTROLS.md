# Governance and Security Controls — Stage 1

**Status:** Design requirements only. No policy engine, approval service, sandbox or security control is claimed to be implemented.

## Trust boundaries

Treat these as separate trust classes:

1. Authenticated user intent and explicit scope.
2. Model/agent suggestions, which are untrusted proposals.
3. Deterministic policy decisions and validated approval records.
4. Synthetic fixture data and outputs from deterministic simulation.
5. User-supplied or observed evidence, each with provenance.
6. Future isolated-lab execution and any real-world system, which are outside Stage 1.

A lower-trust input cannot directly become a privileged action. Natural-language instructions, role names, confidence, or a model-generated explanation do not grant authority.

## Proposed autonomy tiers

| Tier | Name | Permitted behavior | Required boundary |
|---|---|---|---|
| A0 | Observe and explain | Read authorized workspace data and explain it | Read-only; workspace and data-class access checks |
| A1 | Plan | Draft missions, hypotheses, and typed plans | No execution side effects; plan cannot self-authorize |
| A2 | Synthetic simulation | Run deterministic rules against versioned synthetic fixtures | Network, shell, host and real-credential capability absent; policy checked before dispatch |
| A3 | Approved isolated experiment — future | Controlled experiment inside a separately designed lab | Separate threat model, isolation proof, scoped time-bound approval, monitoring and emergency stop; not enabled by Stage 1 |
| A4 | Real-world consequential action | Excluded by default | No general permission in this blueprint; any future proposal requires explicit separate authorization and review |

Tier names communicate the maximum intended autonomy; they are not capability tokens. The runtime must enforce a per-task capability allowlist and deny unexpected capabilities.

## Authorization decision

Before any task is queued or resumed, the execution boundary must check:

- authenticated principal and workspace membership;
- mission status and explicit objective/scope;
- source class and target restrictions;
- task type and declared maximum capability set;
- current deterministic policy version and policy result;
- approval status, approver authority, requester/approver separation when required;
- exact scope and canonical plan digest binding;
- approval expiry, revocation and replay/consumption state;
- resource/time limits and environment classification.

Any missing, ambiguous, expired, unavailable or contradictory input results in **deny / blocked**. A policy-service outage, verifier outage, stale plan, unknown worker state or missing approval never falls back to allow.

## Approval binding

An approval is a structured, auditable record bound to a specific workspace, requester, mission, action class, scope, constraints, canonical plan digest, expiry and decision. Editing the plan or scope invalidates the approval. Approval is checked again immediately before execution; an earlier approval does not transfer automatically to a new mission or run.

Who can approve, whether every synthetic run needs human approval, and the emergency-stop owner remain explicit owner decisions. Regardless of that decision, deterministic scope/policy validation is mandatory.

## Workspace isolation

- Server-side authentication determines the principal; authorization determines accessible workspaces and records.
- Ignore a client-supplied workspace ID for permission decisions; compare it to the server-authorized workspace.
- Apply workspace authorization to every read, write, search, event stream, evidence download, approval and report.
- Verify that relationships cannot link entities across workspaces unless both references are in an explicit, versioned shared-fixture catalog.
- Use negative tests with two workspaces and similar identifiers to detect insecure direct object references.
- Do not disclose whether another workspace contains a requested object.

## Agent and model containment

- Agent roles emit typed proposals and evidence references, not unbounded executable instructions.
- Tool calls require deterministic validation, allowlisted operation names, validated arguments, policy authorization and bounded resources.
- Never execute model-generated shell commands, SQL, network targets or arbitrary code.
- Keep orchestration, approval, execution and independent verification separate. NEXARCH cannot approve its own plan; Origo must not be the same result-producing function for the checks it verifies.
- Specialist agents cannot widen scope, issue approvals, override policy, or change evidence records silently.
- Treat retrieved data and fixture content as potentially adversarial input (prompt injection/data poisoning boundary).

## Evidence integrity and provenance

Every evidence item records source class, source/reference, producer/version, timestamp, mission/task linkage, digest where applicable, parent references and limitations. Distinguish synthetic facts, externally supplied/observed records, hypotheses and verifier conclusions. Corrections append a linked record instead of silently mutating history. Hashes alone do not establish truth or trusted origin.

Audit events should include actor/service identity, action, resource, policy decision, reason code, timestamp, request/correlation ID and object version/reference. Secrets and sensitive personal data must not be copied into audit text unnecessarily.

## Secrets and operational safety

- No secrets in source, client bundles, fixture files, screenshots, reports or ordinary logs.
- Credentials, session tokens and authorization headers are redacted from telemetry.
- Use a server-side secret-management plan before adding providers, credentials or integrations; exact provider is undecided.
- Enforce request size, rate, task-count, mission duration, concurrency, event payload and retry limits.
- Limit task processes and data access to the minimum needed.
- Health endpoints expose only safe readiness information, not secrets or detailed internal topology.
- Record cancellation requests, worker stop acknowledgements and uncertain shutdown states.

## Stage 1 simulation boundary

The initial authentication-failure scenario accepts only versioned synthetic fixtures from a controlled fixture registry. It must not resolve live hosts, contact external networks, test passwords, enumerate accounts, execute commands on a host, or mutate any external environment. A fixture's string fields are data, never commands or URLs to fetch.

Future lab capability requires a separately reviewed design for network isolation, identity/credential boundaries, resource controls, containment, reset/cleanup, monitoring, emergency stop, approval and verification. This document does not enable it.

## Minimum negative tests

- Missing or expired approval; mismatch in scope, plan digest, approver or workspace.
- Policy service unavailable or returns malformed/unknown result.
- Client attempts cross-workspace access or manipulates workspace IDs.
- Agent output proposes shell, SQL, live URL fetch, real credential use or broader scope.
- Evidence is missing provenance, tampered, duplicated or falsely labeled as observed.
- Cancellation arrives while queued or running; a worker stop cannot be confirmed.
- Synthetic runner receives external target/URL, host command or non-synthetic source reference.
- Logs, reports or client assets contain secrets.
