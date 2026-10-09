# Governance and Safety

**Status:** Required design principles; controls are not verified as implemented.

## Authority separation

ERGOUSIARCH is the governing-authority identity in the concept. It should be represented by enforceable policy, approval, and audit services—not by trusting an agent's assertion that an action is allowed.

- **NEXARCH** plans and coordinates; it does not grant itself authority.
- **Kratos** represents policy-enforcement responsibilities.
- **Exousia** represents validation of approvals.
- **Prytanie** represents governance operations and records.
- The execution boundary must independently check the authorization decision before consequential actions.

## Autonomy tiers

1. **Observe and explain:** inspect supplied or synthetic data and explain findings.
2. **Plan:** propose hypotheses, queries, and actions without executing consequential operations.
3. **Simulate:** execute deterministic actions inside the synthetic environment.
4. **Approved isolated experiment:** run only within a separately isolated lab after explicit authorization and preflight checks.
5. **Real-world consequential action:** excluded from default autonomy; requires separately defined authorization, safeguards, and explicit scope. No general permission is implied by the concept.

## Approval record

For consequential actions, record the requesting principal, approving principal, mission, target scope, permitted operation, rationale, timestamp, expiry, policy version, and result. Approval must be bound to a specific action or bounded plan; it must not be a reusable blanket authorization. The approver must have authority and should not be the agent whose action is being approved.

## Mandatory controls

- Authentication and workspace authorization.
- Scope allowlists and explicit exclusions.
- Machine-checkable policy decisions at the execution boundary.
- Least privilege and short-lived credentials.
- Resource, time, and action budgets.
- Explicit approval for consequential operations.
- Audit events for policy decisions, approvals, tool calls, state changes, and verification.
- Cancellation, timeout, cleanup, and fail-closed behavior.
- Validation and sanitization of all model-generated arguments.
- Secret handling that avoids exposing credentials in prompts, logs, or evidence.
- Clear labels separating simulated, synthetic, inferred, and observed evidence.

## Lab isolation requirements

A future lab must be separated from the control plane and ordinary user environment. Its design should define network egress restrictions, identity and credential boundaries, disposable or resettable workloads, resource limits, artifact handling, logging, cleanup, and a verified stop mechanism. No lab implementation should be considered ready merely because containers or virtual machines are mentioned in a plan.

## Independent verification

Verification must be an independent check against evidence, baseline, expected outcomes, or a deterministic oracle. Rephrasing the originating agent's explanation is not verification. A verifier must be able to return failed, disputed, incomplete, or inconclusive outcomes.

## Audit and retention

Audit records should be attributable, timestamped, tamper-resistant to the extent supported by the implementation, and linked to mission/task/evidence IDs. Define retention, deletion, access controls, and sensitive-data minimization before handling real user or organization data.

## Safety acceptance gates

Do not move to the next stage unless:
- Scope and authorization checks are testable.
- Unauthorized actions are denied at the execution boundary.
- Simulation is visibly separated from real-world execution.
- Evidence and approvals are auditable.
- Cancellation and cleanup have been tested.
- The verifier can reject an unsupported claim.
- Failure paths fail closed.

These are requirements for future implementation and validation, not claims that NEXORION currently satisfies them.
