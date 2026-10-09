# Suggested additive section for `docs/SOURCE_OF_TRUTH.md`

Append this section on `stag1`; preserve all existing entries and caveats above it.

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
