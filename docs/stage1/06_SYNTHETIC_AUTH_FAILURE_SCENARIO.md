# First Vertical Slice — Synthetic Authentication-Failure Investigation

**Status:** Testable scenario specification; no scenario runner or product implementation is claimed.

## Objective

Demonstrate a complete, repeatable mission using fabricated authentication events: validate synthetic-only scope, establish a versioned baseline, apply a deterministic rule, produce provenance-linked evidence, independently verify the outcome and generate a report with clear limitations.

This is not a penetration test. It does not try passwords, contact services, scan networks, inspect production telemetry or change any system.

## Fixed safety constraints

- Inputs come only from version-controlled synthetic fixtures or an ephemeral fixture generator.
- Use inert fictional identities such as `user-001@example.invalid`.
- IP examples are inert fixture fields from documentation ranges (for example, `203.0.113.0/24)); they must never cause a network request.
- No passwords, tokens, session cookies or production identifiers are stored.
- Scenario code has no network or operating-system command capability.
- Results are deterministic for the same fixture and rule-set versions.

## Fixture A — suspicious pattern

All event times are relative to the synthetic scenario start. Values are fabricated.

| Event | Offset | Principal | Source IP field | Outcome | Note |
|---|---:|---|---|---|---|
| E1 | +00:00:00 | `user-001@example.invalid` | `203.0.113.17` | `failure` | Attempt 1 |
| E2 | +00:00:08 | `user-001@example.invalid` | `203.0.113.17` | `failure` | Attempt 2 |
| E3 | +00:00:16 | `user-001@example.invalid` | `203.0.113.17` | `failure` | Attempt 3 |
| E4 | +00:00:24 | `user-001@example.invalid` | `203.0.113.17` | `failure` | Attempt 4 |
| E5 | +00:00:32 | `user-001@example.invalid` | `203.0.113.17` | `failure` | Attempt 5 |
| E6 | +00:00:44 | `user-001@example.invalid` | `203.0.113.17` | `success` | Success follows repeated failures |

The IP field is synthetic event data only.

## Deterministic rule: `auth-failure-rules-v1`

1. Group events by fixture-defined synthetic principal and source IP.
2. Sort by timestamp, using event ID as a stable tie-breaker.
3. Count `failure` outcomes in the inclusive rolling 10-minute window ending at each event.
4. If a `success` event has at least five preceding failures in that window for the same group, emit `suspicious_auth_pattern` and cite supporting event IDs.
5. If there is no success after five failures, emit `repeated_auth_failures`; do not imply successful account access.
6. Missing required fields, unparseable times, invalid ordering or non-synthetic provenance produces validation failure or `inconclusive`, never a guessed result.

This is a teaching rule, not a claim that five failures prove malicious behavior in a real environment. Real-source calibration is out of scope.

## Control fixtures

- **Fixture B — benign control:** three failures for `user-002@example.invalid` within 10 minutes and no success. Expected: `repeated_auth_failures`, not `suspicious_auth_pattern`.
- **Fixture C — malformed/provenance-negative control:** missing principal and at least one event labeled `observed` while the mission requires synthetic-only inputs. Expected: rejection or `inconclusive`; no execution and no verified result.

## Mission sequence and role boundaries

1. **Monarque:** capture objective, assumptions and synthetic-only scope.
2. **NEXARCH:** create a bounded plan containing only fixture read, deterministic rule evaluation, evidence capture and report generation.
3. **Policy/approval services:** validate workspace, scope, autonomy tier, source class, rule version and any required approval. Denial blocks dispatch.
4. **Ab-Initio:** capture a versioned baseline reference and fixture-state digest.
5. **Genesis/Genarch:** select the fixed scenario and fixture set; do not generate live targets.
6. **Protos:** apply the deterministic rule and record rule-set version plus input digest.
7. **Mneme:** index immutable provenance-linked evidence.
8. **Origo:** independently check provenance, rule/version, supporting event IDs, expected classification, absence of external execution and consistency of report references.
9. **NEXARCH:** assemble the report only after a verification result is available; state limits and incomplete checks.

This is a logical responsibility mapping. Each role need not be a separate LLM or process in the first implementation.

## Required evidence

- Mission request and validated scope.
- Scenario/fixture version and digest.
- Baseline record and digest.
- Rule result with supporting event IDs and rule version.
- Runtime/test evidence that no network or host-execution capability was available; a self-authored statement alone is not proof.
- Independent verifier checks and status.
- Final report linking claims to evidence and stating the synthetic-only limit.

## Expected outcomes

| Case | Expected output | Verification condition |
|---|---|---|
| Fixture A | `suspicious_auth_pattern` | Verified only if mandatory rule and provenance checks pass |
| Fixture B | `repeated_auth_failures` | Verified when output matches the rule and evidence is complete |
| Fixture C | Rejected or `inconclusive` | Must never be reported as verified/succeeded |
| Policy unavailable | Block/fail closed; no dispatch | Record dependency failure; fabricate no result |
| Plan changes after required approval | `blocked_approval`; no execution | Record digest mismatch |
| Origo finds missing evidence/contradiction | `disputed` or `inconclusive` | Mission cannot transition to `succeeded` |

## Definition of done for the future implementation

- All three fixture cases are deterministic and versioned.
- Suspicious and benign cases produce expected outputs.
- Report claims reference evidence or are explicitly labeled assumptions.
- Synthetic run cannot resolve hostnames or connect to networks.
- Invalid provenance, unavailable policy, changed approval digest and verifier failure block success.
- Idempotent run requests do not duplicate task execution or evidence.
- Report explicitly says synthetic evidence is not evidence of real-world activity.

These are acceptance tests to implement later; no runtime test has passed by virtue of this specification.
