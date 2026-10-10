"""Independent, persisted-evidence verification for registered synthetic scenarios."""

from collections.abc import Sequence
from typing import Any

from app.simulation import digest

ORIGO_VERIFIER_VERSION = "origo-synthetic-evidence-v1.0"
ORIGO_SCHEMA_VERSION = "1.0"
SUPPORTED_SCENARIOS = {
    "scenario-auth-failure-v1": {
        "fixture_version": "1.0.0",
        "rule_set_version": "auth-failure-rules-v1",
    },
    "scenario-auth-benign-control-v1": {
        "fixture_version": "1.0.0",
        "rule_set_version": "auth-failure-rules-v1",
    },
}
LIMITATIONS = [
    "Verification covers persisted synthetic evidence only; no live system or "
    "external telemetry is inspected.",
    "The authentication threshold is a teaching rule and is not calibrated "
    "for real-world detection.",
    "A verified synthetic result is not proof of real-world malicious activity or compromise.",
]


def _check(check: str, passed: bool | None, reason: str) -> dict[str, object]:
    return {"check": check, "passed": passed, "reason": reason}


def _analyse_events(events: list[dict[str, object]]) -> tuple[str, list[str]]:
    """Independently evaluate persisted event data without loading fixture outcomes."""
    ordered = sorted(events, key=lambda item: (int(item["offset_seconds"]), str(item["event_id"])))
    for event in ordered:
        if event.get("outcome") != "success":
            continue
        offset = int(event["offset_seconds"])
        principal = event["principal"]
        source_ip = event["source_ip"]
        preceding = [
            prior for prior in ordered
            if prior.get("outcome") == "failure"
            and prior.get("principal") == principal
            and prior.get("source_ip") == source_ip
            and 0 <= offset - int(prior["offset_seconds"]) <= 600
        ]
        if len(preceding) >= 5:
            return "suspicious_auth_pattern", [
                str(item["event_id"]) for item in preceding[-5:]
            ] + [str(event["event_id"])]
    failures = [item for item in ordered if item.get("outcome") == "failure"]
    if failures:
        return "repeated_auth_failures", [str(item["event_id"]) for item in failures]
    return "no_pattern_detected", []


def evaluate_persisted_run(run: Any, evidence_records: Sequence[Any]) -> dict[str, object]:
    """Return checks and status based only on persisted run/evidence rows."""
    checks: list[dict[str, object]] = []
    reasons: list[str] = []
    discrepancies: list[dict[str, object]] = []
    failed = False
    disputed = False
    insufficient = False
    evidence_ids = [str(item.id) for item in evidence_records]
    fingerprints = {str(item.id): str(item.content_digest) for item in evidence_records}

    checks.append(_check("evidence_present", bool(evidence_records),
        "Persisted evidence records are available." if evidence_records
        else "No evidence is linked to this run."))
    if not evidence_records:
        insufficient = True
        reasons.append("No persisted evidence exists for this run.")

    valid_payloads: list[tuple[Any, dict[str, object]]] = []
    for item in evidence_records:
        association_ok = (
            item.workspace_id == run.workspace_id
            and item.mission_id == run.mission_id
            and item.run_id == run.id
        )
        checks.append(_check("evidence_association:" + str(item.id), association_ok,
            "Evidence workspace, mission and run references match."
            if association_ok else "Evidence references do not match the owning run."))
        if not association_ok:
            failed = True
            reasons.append(
                "An evidence record has an inconsistent workspace, mission or "
                "run association."
            )

        payload = item.payload if isinstance(item.payload, dict) else None
        digest_ok = payload is not None and digest(payload) == item.content_digest
        checks.append(_check("evidence_fingerprint:" + str(item.id), digest_ok,
            "SHA-256 content fingerprint matches the stored payload."
            if digest_ok else "Stored evidence payload does not match its content fingerprint."))
        if not digest_ok:
            failed = True
            reasons.append("At least one evidence payload failed its content-integrity check.")

        if item.source_class != "synthetic":
            failed = True
            checks.append(_check("synthetic_provenance:" + str(item.id), False,
                "Evidence source class is not synthetic."))
            reasons.append("Evidence source class violates the synthetic-only boundary.")
        elif not item.source_ref or not item.producer or not item.producer_version:
            insufficient = True
            checks.append(_check("synthetic_provenance:" + str(item.id), None,
                "Provenance fields are incomplete."))
            reasons.append("Evidence provenance is incomplete.")
        else:
            checks.append(_check("synthetic_provenance:" + str(item.id), True,
                "Synthetic source, source reference, producer and producer version are present."))

        if payload is not None and association_ok:
            valid_payloads.append((item, payload))

    event_entry = next(
        (
            (item, payload)
            for item, payload in valid_payloads
            if isinstance(payload.get("events"), list)
        ),
        None,
    )
    if event_entry is None:
        insufficient = True
        checks.append(_check("event_payload_complete", None,
            "Persisted evidence does not contain event detail needed by this verifier."))
        reasons.append("Event-level evidence is missing or legacy; verification is inconclusive.")
        events: list[dict[str, object]] = []
        event_payload: dict[str, object] = {}
    else:
        _, event_payload = event_entry
        raw_events = event_payload.get("events")
        assert isinstance(raw_events, list)
        events = [item for item in raw_events if isinstance(item, dict)]
        schema_ok = (
            event_payload.get("payload_schema_version") == "1.0"
            and len(events) == len(raw_events)
            and bool(events)
        )
        if not schema_ok:
            insufficient = True
            checks.append(_check("event_payload_complete", None,
                "Event detail is empty, malformed or uses an unsupported evidence schema."))
            reasons.append("The persisted event payload is incomplete or unsupported.")
        else:
            checks.append(_check("event_payload_complete", True,
                "Event-level records and supported payload schema are present."))

    evaluated_outcome: str | None = None
    evaluated_supporting_ids: list[str] = []
    if events and not insufficient:
        ids = [item.get("event_id") for item in events]
        unique_ids = all(isinstance(value, str) for value in ids) and len(ids) == len(set(ids))
        event_shapes_ok = all(
            isinstance(event.get("event_id"), str) and bool(event.get("event_id"))
            and isinstance(event.get("offset_seconds"), int)
            and event.get("offset_seconds", -1) >= 0
            and isinstance(event.get("principal"), str) and bool(event.get("principal"))
            and isinstance(event.get("source_ip"), str) and bool(event.get("source_ip"))
            and event.get("outcome") in {"failure", "success"}
            for event in events
        )
        ordered = all(
            (int(events[index - 1]["offset_seconds"]), str(events[index - 1]["event_id"]))
            <= (int(events[index]["offset_seconds"]), str(events[index]["event_id"]))
            for index in range(1, len(events))
        ) if event_shapes_ok else False
        count_ok = event_payload.get("event_count") == len(events)
        if not unique_ids or not event_shapes_ok or not count_ok:
            failed = True
            checks.append(_check("event_record_integrity", False,
                "Event IDs, required fields or recorded event count are inconsistent."))
            reasons.append("Persisted event structure or event count failed validation.")
        else:
            checks.append(_check("event_record_integrity", True,
                "Event identifiers, required fields and recorded count are consistent."))
        checks.append(_check("event_sequence_consistency", ordered,
            "Events are in deterministic nondecreasing sequence order."
            if ordered else "Events are out of sequence or cannot be ordered safely."))
        if not ordered:
            failed = True
            reasons.append("Persisted event sequence is inconsistent.")

        support_refs = event_payload.get("supporting_event_ids")
        references_ok = (
            isinstance(support_refs, list)
            and all(isinstance(value, str) for value in support_refs)
            and set(support_refs).issubset(set(value for value in ids if isinstance(value, str)))
        )
        checks.append(_check("supporting_event_references", references_ok,
            "Every supporting event reference resolves to a persisted event."
            if references_ok else "A supporting event reference is missing or unresolved."))
        if not references_ok:
            failed = True
            reasons.append("Evidence references events that do not exist in the persisted payload.")

        scenario = SUPPORTED_SCENARIOS.get(str(run.scenario_id))
        compatible = (
            scenario is not None
            and run.fixture_version == scenario["fixture_version"]
            and run.rule_set_version == scenario["rule_set_version"]
            and event_payload.get("scenario_id") == run.scenario_id
            and event_payload.get("fixture_version") == run.fixture_version
            and event_payload.get("rule_set_version") == run.rule_set_version
        )
        checks.append(_check("scenario_verifier_compatibility", compatible,
            "Scenario, fixture and rule-set versions are supported."
            if compatible else "Scenario or version metadata is missing or unsupported."))
        if not compatible:
            insufficient = True
            reasons.append(
                "The evidence does not match a scenario/version supported by "
                "this verifier."
            )

        if event_shapes_ok and unique_ids and count_ok and ordered and compatible:
            try:
                evaluated_outcome, evaluated_supporting_ids = _analyse_events(events)
            except (KeyError, TypeError, ValueError, OverflowError):
                failed = True
                reasons.append("Persisted events could not be evaluated safely.")
            if evaluated_outcome is not None:
                run_claim_matches = run.outcome == evaluated_outcome
                payload_claim_matches = event_payload.get("outcome") == evaluated_outcome
                checks.append(
                    _check(
                        "independent_outcome_matches_run",
                        run_claim_matches,
                        "Persisted events support the run outcome."
                        if run_claim_matches
                        else "Run outcome conflicts with independent event analysis.",
                    )
                )
                checks.append(
                    _check(
                        "independent_outcome_matches_evidence",
                        payload_claim_matches,
                        "Persisted events support the evidence outcome."
                        if payload_claim_matches
                        else "Evidence outcome conflicts with independent event analysis.",
                    )
                )
                if not run_claim_matches or not payload_claim_matches:
                    disputed = True
                    discrepancies.append({
                        "type": "outcome_conflict", "run_outcome": str(run.outcome),
                        "evidence_outcome": str(event_payload.get("outcome", "missing")),
                        "independent_outcome": evaluated_outcome,
                    })
                    reasons.append(
                        "Recorded outcome claims conflict with the independently "
                        "evaluated events."
                    )
                support_matches = (
                    event_payload.get("supporting_event_ids") == evaluated_supporting_ids
                )
                checks.append(
                    _check(
                        "supporting_events_match_analysis",
                        support_matches,
                        "Supporting-event references match independent event analysis."
                        if support_matches
                        else "Supporting-event references differ from independent analysis.",
                    )
                )
                if not support_matches:
                    disputed = True
                    discrepancies.append({
                        "type": "supporting_event_conflict",
                        "recorded": event_payload.get("supporting_event_ids"),
                        "independent": evaluated_supporting_ids,
                    })
                    reasons.append(
                        "Supporting-event references conflict with independent "
                        "event analysis."
                    )

    if event_entry is not None:
        payload = event_entry[1]
        input_fields_present = all(payload.get(field) is not None for field in
            ("scenario_id", "fixture_version", "rule_set_version", "events"))
        if input_fields_present:
            expected_input = digest({
                "scenario_id": run.scenario_id, "fixture_version": run.fixture_version,
                "rule_set_version": run.rule_set_version, "events": payload["events"],
            })
            input_matches = run.input_digest == expected_input
            checks.append(_check("run_input_fingerprint", input_matches,
                "Run input fingerprint matches persisted event input."
                if input_matches else "Run input fingerprint differs from persisted event input."))
            if not input_matches:
                failed = True
                reasons.append("Stored run input fingerprint does not match persisted evidence.")
        else:
            insufficient = True
            checks.append(_check("run_input_fingerprint", None,
                "Legacy evidence lacks fields needed to reconstruct the input fingerprint."))

    if isinstance(run.result, dict) and run.output_digest:
        output_matches = digest(run.result) == run.output_digest
        checks.append(_check("run_output_fingerprint", output_matches,
            "Run output fingerprint matches the persisted result."
            if output_matches else "Persisted run result does not match its output fingerprint."))
        if not output_matches:
            failed = True
            reasons.append("Stored run output fingerprint does not match the persisted result.")
    else:
        insufficient = True
        checks.append(_check("run_output_fingerprint", None,
            "Run result or output fingerprint is unavailable."))

    if failed:
        status = "failed"
    elif disputed:
        status = "disputed"
    elif insufficient or evaluated_outcome is None:
        status = "inconclusive"
    else:
        status = "verified"
        reasons.append(
            "Persisted synthetic events passed integrity, provenance, sequence "
            "and independent rule evaluation."
        )

    return {
        "status": status, "verifier_version": ORIGO_VERIFIER_VERSION,
        "schema_version": ORIGO_SCHEMA_VERSION,
        "checks": checks,
        "reasons": reasons or ["No verification reason was produced."],
        "discrepancies": discrepancies, "evidence_ids": evidence_ids,
        "evidence_fingerprints": fingerprints, "limitations": list(LIMITATIONS),
        "independent_outcome": evaluated_outcome,
    }
