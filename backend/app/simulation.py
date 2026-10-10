"""Deterministic synthetic authentication-event fixtures and rule evaluation.

This module intentionally contains no network, subprocess, filesystem-execution, or
credential-attempt capability. Fixture values are inert data only.
"""

import hashlib
import json
from typing import Any


RULE_SET_VERSION = "auth-failure-rules-v1"
SIMULATOR_VERSION = "0.1.0"
LIMITATIONS = [
    "All input records are synthetic and do not describe a real environment.",
    "The five-failure teaching threshold is not calibrated for real-world detection.",
    "A simulated classification is not proof of malicious activity or account compromise.",
]


SCENARIO_REGISTRY: dict[str, dict[str, Any]] = {
    "scenario-auth-failure-v1": {
        "fixture_version": "1.0.0",
        "source_ref": "fixture://auth-failure/sequence-a",
        "expected_outcome": "suspicious_auth_pattern",
        "events": [
            {"event_id": "E1", "offset_seconds": 0,
                "principal": "user-001@example.invalid", "source_ip": "203.0.113.17", "outcome": "failure"},  # noqa: E501
            {"event_id": "E2", "offset_seconds": 8,
                "principal": "user-001@example.invalid", "source_ip": "203.0.113.17", "outcome": "failure"},  # noqa: E501
            {"event_id": "E3", "offset_seconds": 16,
                "principal": "user-001@example.invalid", "source_ip": "203.0.113.17", "outcome": "failure"},  # noqa: E501
            {"event_id": "E4", "offset_seconds": 24,
                "principal": "user-001@example.invalid", "source_ip": "203.0.113.17", "outcome": "failure"},  # noqa: E501
            {"event_id": "E5", "offset_seconds": 32,
                "principal": "user-001@example.invalid", "source_ip": "203.0.113.17", "outcome": "failure"},  # noqa: E501
            {"event_id": "E6", "offset_seconds": 44,
                "principal": "user-001@example.invalid", "source_ip": "203.0.113.17", "outcome": "success"},  # noqa: E501
        ],
    },
    "scenario-auth-benign-control-v1": {
        "fixture_version": "1.0.0",
        "source_ref": "fixture://auth-failure/sequence-b",
        "expected_outcome": "repeated_auth_failures",
        "events": [
            {"event_id": "B1", "offset_seconds": 0,
                "principal": "user-002@example.invalid", "source_ip": "203.0.113.27", "outcome": "failure"},  # noqa: E501
            {"event_id": "B2", "offset_seconds": 12,
                "principal": "user-002@example.invalid", "source_ip": "203.0.113.27", "outcome": "failure"},  # noqa: E501
            {"event_id": "B3", "offset_seconds": 28,
                "principal": "user-002@example.invalid", "source_ip": "203.0.113.27", "outcome": "failure"},  # noqa: E501
        ],
    },
}


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: object) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def get_fixture(scenario_id: str) -> dict[str, Any] | None:
    fixture = SCENARIO_REGISTRY.get(scenario_id)
    if fixture is None:
        return None
    # Return a detached value so callers cannot mutate the server registry.
    return json.loads(json.dumps(fixture))


def evaluate_fixture(scenario_id: str, fixture: dict[str, Any]) -> dict[str, Any]:
    events = sorted(fixture["events"], key=lambda item: (item["offset_seconds"], item["event_id"]))
    matching_failures: list[dict[str, Any]] = []
    chosen_success: dict[str, Any] | None = None
    for event in events:
        if event["outcome"] != "success":
            continue
        preceding = [
            prior for prior in events
            if prior["outcome"] == "failure"
            and prior["principal"] == event["principal"]
            and prior["source_ip"] == event["source_ip"]
            and 0 <= event["offset_seconds"] - prior["offset_seconds"] <= 600
        ]
        if len(preceding) >= 5:
            chosen_success = event
            matching_failures = preceding[-5:]
            break

    if chosen_success is not None:
        outcome = "suspicious_auth_pattern"
        supporting_ids = (
            [item["event_id"] for item in matching_failures]
            + [chosen_success["event_id"]]
        )
        summary = (
            "A synthetic success followed at least five matching failures "
            "inside the configured window."
        )
    else:
        failures = [item for item in events if item["outcome"] == "failure"]
        if failures:
            outcome = "repeated_auth_failures"
            supporting_ids = [item["event_id"] for item in failures]
            summary = (
                "Repeated synthetic authentication failures were recorded without "
                "the required success-after-threshold pattern."
            )
        else:
            outcome = "no_pattern_detected"
            supporting_ids = []
            summary = "The fixed synthetic fixture did not match the configured teaching rule."

    return {
        "scenario_id": scenario_id,
        "outcome": outcome,
        "summary": summary,
        "rule_set_version": RULE_SET_VERSION,
        "event_count": len(events),
        "supporting_event_ids": supporting_ids,
        "source_class": "synthetic",
        "limitations": list(LIMITATIONS),
    }


def verify_fixture_result(scenario_id: str, fixture: dict[str, Any], result: dict[str,
    Any]) -> dict[str, Any]:
    event_ids = {item["event_id"] for item in fixture["events"]}
    referenced_ids = result.get("supporting_event_ids", [])
    checks = [
        {"check": "registered_fixture_only", "passed": scenario_id in SCENARIO_REGISTRY},
        {"check": "synthetic_source_label", "passed": result.get("source_class") == "synthetic"},
        {"check": "fixture_event_count",
            "passed": result.get("event_count") == len(fixture["events"])},
        {"check": "expected_fixture_outcome",
            "passed": result.get("outcome") == fixture["expected_outcome"]},
        {"check": "evidence_references_resolve", "passed": isinstance(referenced_ids,
            list) and set(referenced_ids).issubset(event_ids)},
    ]
    return {
        "status": "verified" if all(item["passed"] for item in checks) else "inconclusive",
        "checks": checks,
        "scope": "deterministic fixture assertions only",
        "limitations": [
            "This is a bounded fixture-consistency check, not a full independent "
    "real-world verifier.",
            "It does not validate any live system, external telemetry, or "
    "operational security claim.",
        ],
    }
