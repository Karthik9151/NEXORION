# Stage 3 — Digital World and Deterministic Simulation

**Branch:** stage3-digital-world  
**Status:** Verified for this bounded Stage 3 scope on commit `04b13f4a3f21e07c242e268fe45ab7396ab4954a`. GitHub Actions passed Python 3.11/3.12 API tests and Ruff, fresh SQLite migration upgrade/downgrade/re-upgrade, PostgreSQL 16 migration upgrade/downgrade/re-upgrade, and a PostgreSQL-backed API smoke test. [Verification run](https://github.com/Karthik9151/NEXORION/actions/runs/38026378118). This does not certify production readiness.

Stage 3 turns the Stage 2 authenticated API foundation into a small, executable digital-world vertical slice. The first version intentionally supports synthetic records and registered fixtures only.

## Delivered capabilities

1. **Synthetic world entities** — create and list typed entities in the selected workspace. Each record is labeled synthetic and stored with schema version, environment, attributes, creator and timestamps.
2. **Typed relationships** — create and list allowed graph edges between two entities in the same workspace. Cross-workspace references and self-edges are rejected.
3. **Versioned baseline snapshots** — capture a mission-scoped snapshot of the allowed graph, record a canonical SHA-256 digest and retain each snapshot sequence. Simulation checks the stored digest before it runs.
4. **Registered deterministic scenarios** — run the fixed authentication-failure scenario or a benign control fixture. The caller cannot upload executable code, arbitrary rules, event records or network targets.
5. **Evidence and reproducibility metadata** — each run records its baseline, fixture and rule versions, input/output digests, outcome, timestamps and provenance-labeled evidence.
6. **Bounded mission execution gate** — running requires an authenticated workspace member, a CSRF check, a mission explicitly configured for simulate_synthetic, a scenario listed in mission scope, a baseline, and a valid idempotency key. A rerun with the same key returns its original run.
7. **Audited outcomes and assertion checks** — the synchronous simulation records mission state transitions and applies fixed-fixture consistency checks. This checker is intentionally narrower than the future full Origo independent-verification system.

## API surface

| Method | Endpoint | Purpose |
|---|---|---|
| POST | /v1/world/entities | Add a synthetic entity |
| GET | /v1/world/entities | List entities in the selected workspace |
| POST | /v1/world/relationships | Add an in-workspace graph edge |
| GET | /v1/world/relationships | List graph edges in the selected workspace |
| POST | /v1/missions/{mission_id}/baselines | Capture a versioned graph snapshot |
| GET | /v1/missions/{mission_id}/baselines | Read mission baselines |
| POST | /v1/missions/{mission_id}/simulate | Run a registered synthetic scenario |
| GET | /v1/missions/{mission_id}/runs | List completed simulation runs and evidence |

All routes are under the existing authenticated /v1 API. Mutating endpoints use the existing CSRF requirement and server-side workspace membership enforcement.

## First scenarios

- scenario-auth-failure-v1: six fictional events, five failures followed by success within the fixed ten-minute rule window. Expected teaching-rule outcome: suspicious_auth_pattern.
- scenario-auth-benign-control-v1: three fictional failures and no following success. Expected outcome: repeated_auth_failures, not the suspicious-success finding.

The fixtures use .invalid identities and documentation-range IP fields as inert strings. These values are data only; the scenario engine does not resolve or contact them.

## Local validation

From backend/:

~~~bash
python -m pip install -e '.[test]'
alembic upgrade head
pytest
ruff check app tests alembic
~~~

The new tests cover workspace isolation, relationship constraints, secret-like attribute rejection, baseline versioning and digests, mission autonomy/scope requirements, missing-baseline blocking, deterministic outcomes, evidence provenance, idempotent execution and the benign control.

## Boundaries and remaining work

This stage does **not** implement a visual graph editor, live asset discovery, telemetry ingestion, uploaded/custom scenarios, arbitrary simulation code, model-backed agents, a durable worker queue, WebSockets, a full Origo verifier, or an isolated cyber range. It has no network-scanning, shell/subprocess, real-credential or live-system mutation route.

The current fixture checker reports whether deterministic assertions agree with the registered fixture; it is not proof about a real system and should not be described as full independent verification. Stage 4 should deepen evidence integrity and independent verification, including tamper and contradiction cases. General-purpose durable workflows, approvals and recovery remain later roadmap work.

## Acceptance gate

**Acceptance evidence completed for this stage's defined scope:** GitHub Actions passed on the branch; fresh SQLite and PostgreSQL 16 migrations upgraded, downgraded to `0001_initial`, and re-upgraded to head; the PostgreSQL API smoke test exercised registration, mission creation, baseline capture, and a synthetic simulation; the API regression suite and Ruff passed on Python 3.11 and 3.12. The reviewed tests cover cross-workspace graph boundaries, CSRF, scope/tier restrictions, baseline prerequisites, secret-like attribute rejection, idempotency, and the benign-control fixture. This is not a full penetration test, concurrency test, backup/restore test, or production certification.
