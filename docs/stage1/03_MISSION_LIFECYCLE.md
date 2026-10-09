# Mission Lifecycle and Recovery Rules

**Status:** Proposed finite-state contract. Implementation and state persistence are not yet verified.

## States

| State | Meaning | May execute work? | Terminal? |
|---|---|---:|---:|
| `draft` | Editable mission request; not validated. | No | No |
| `validating` | Server checks schema, workspace, scope and policy prerequisites. | No | No |
| `blocked_scope` | Scope is missing, ambiguous, or invalid. | No | No |
| `blocked_approval` | Required approval is missing, expired, or mismatched. | No | No |
| `rejected` | Deterministic policy explicitly denied the mission. | No | Yes |
| `ready` | Required validation succeeded; execution has not begun. | No | No |
| `planning` | Producing a typed, non-executing plan. | Planning only | No |
| `planned` | Immutable, versioned plan and digest recorded. | No | No |
| `queued` | Authorized synthetic run accepted for scheduling. | Not yet | No |
| `running` | Bounded tasks are running within approved capabilities. | Within scope only | No |
| `cancelling` | New work stopped; active work is receiving cancellation. | No new work | No |
| `verifying` | Independent validation of task outputs and evidence. | Verification only | No |
| `succeeded` | Required tasks completed and independent verifier returned `verified`. | No | Yes |
| `completed_with_warnings` | Required checks passed with permitted non-critical limitations. | No | Yes |
| `disputed` | A contradiction or mandatory check failure was found. | No | Yes |
| `inconclusive` | Evidence is insufficient to establish the expected result. | No | Yes |
| `failed` | Unrecoverable technical or contract failure. | No | Yes |
| `cancelled` | Cancellation completed; partial work/evidence retained. | No | Yes |
| `expired` | A mission, approval, or task lifetime expired before completion. | No | Yes |

Blocked states are visible, non-terminal waits. No task is dispatched while blocked. A blocked mission resumes only after explicit revalidation.

## Allowed transitions

| From | To | Trigger and required guard |
|---|---|---|
| `draft` | `validating` | Authenticated caller requests validation; request limits pass. |
| `validating` | `blocked_scope` | Scope, schema, or ownership cannot be validated. |
| `validating` | `blocked_approval` | Required approval is absent or invalid. |
| `validating` | `rejected` | Deterministic policy explicitly denies the request. |
| `validating` | `ready` | Validation succeeds and policy permits planning. |
| `blocked_scope` | `validating` | Corrected scope submitted; full validation repeats. |
| `blocked_approval` | `validating` | Approval is added/updated; full validation repeats. |
| `ready` | `planning` | Explicit plan request and authorization to plan. |
| `planning` | `planned` | Valid typed plan is produced and canonical digest stored. |
| `planning` | `failed` | Plan violates contract or bounded attempts are exhausted. |
| `planned` | `blocked_approval` | Approval is required or its digest does not match this plan. |
| `planned` | `queued` | Explicit run request; policy, approval, expiry and digest rechecked. |
| `queued` | `running` | Scheduler obtains a valid lease and rechecks authorization. |
| `queued` | `cancelled` | Cancellation wins before work begins. |
| `running` | `cancelling` | Authorized cancellation, emergency stop, or policy-required stop. |
| `running` | `verifying` | All mandatory tasks reach defined terminal outcomes. |
| `running` | `failed` | Non-recoverable worker, policy, or contract failure. |
| `running` | `expired` | Policy prohibits continuation after expiry. |
| `cancelling` | `cancelled` | Work stopped or reached recorded safe termination. |
| `cancelling` | `failed` | Safe termination cannot be established before deadline; emit high-severity audit event. |
| `verifying` | `succeeded` | All mandatory checks pass and verifier says `verified`. |
| `verifying` | `completed_with_warnings` | Mandatory checks pass; permitted non-critical issues remain. |
| `verifying` | `disputed` | Contradiction or mandatory check failure. |
| `verifying` | `inconclusive` | Required evidence is missing or insufficient. |
| `verifying` | `failed` | Verification service fails and retry budget is exhausted; fail closed. |

No other mission transitions are permitted. Attempt-level retries do not reopen terminal missions; reruns use new mission/run identities linked to the prior record.

## Transition invariants

- Transitions are server-side commands, never direct client writes to `state`.
- Every transition records old/new state, actor or service, timestamp, reason code, request ID and object version.
- Optimistic concurrency/version checks prevent incompatible simultaneous state changes.
- Entry to `queued` and `running` requires an execution-time check of workspace, target scope, policy, current approval, plan digest, expiry and allowed capabilities.
- Any uncertainty in authorization prevents queueing or execution.
- Terminal records have a terminal timestamp and completion reason and cannot be reopened by mutation.

## Task retry, deduplication and leases

1. Retry only classified transient failures; never automatically retry scope, validation or policy-denial errors.
2. Use bounded exponential backoff with jitter; concrete defaults are an operations decision.
3. Each attempt records a unique attempt ID, error category, start/end timestamps and evidence references.
4. A task with side effects must declare idempotency semantics. If safe replay is unknown, block for review instead of replaying.
5. Lease expiry permits reassignment only after the previous worker's capabilities are revoked or its execution environment is known stopped. A timeout alone does not prove a worker stopped.
6. Duplicate delivery must not duplicate evidence or run consequential actions twice. Define idempotency-key uniqueness scope.

## Cancellation

- Cancellation is idempotent: repeat requests return the current cancellation state.
- Stop dispatching new tasks as soon as cancellation is accepted.
- Signal running workers and use a bounded grace period. A worker that will not stop requires a separately designed isolation/termination mechanism and an explicit failure record.
- Preserve partial evidence and identify tasks that completed, stopped, timed out or remain uncertain.
- Cancellation must not silently delete the mission or its audit history. Retention/deletion remains an owner decision.

## Recovery and restart

- Durable state is authoritative; in-memory worker state is not.
- After restart, reconcile leases, attempts, approvals and mission states before dispatching work.
- Revalidate authorization before a recovered task resumes.
- Stale approval, changed scope/plan digest, missing evidence, or unknown execution status causes a blocked/fail-closed result pending review.
- The workflow engine is undecided; these semantics apply regardless of the eventual implementation.

## Required lifecycle test cases

- Valid missions advance only through permitted transitions; clients cannot set state directly.
- Missing, expired or mismatched approval blocks a run.
- Plan changes after approval invalidate the approval binding.
- Duplicate run requests do not create duplicate work.
- Policy-service timeout prevents queueing.
- Cancellation while queued starts no task; cancellation while running preserves partial evidence.
- Worker crash/lease expiry cannot duplicate non-idempotent execution.
- `disputed` or `inconclusive` verification never yields success.
- Workspace authorization is rechecked for read, cancel, approval and report operations.
