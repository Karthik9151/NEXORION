"""Scenario catalog, persisted Origo verification and authorized mission reports."""

import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, Request, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_csrf, require_workspace_membership
from app.errors import ApiError
from app.models import (
    AuditEvent,
    EvidenceRecord,
    Mission,
    OrigoVerification,
    SimulationRun,
    User,
    WorldSnapshot,
    new_id,
)
from app.origo import LIMITATIONS, ORIGO_VERIFIER_VERSION, evaluate_persisted_run
from app.services.lifecycle import transition_mission
from app.schemas import VerificationHistoryPublic, VerificationPublic
from app.simulation import RULE_SET_VERSION, SCENARIO_REGISTRY

router = APIRouter(tags=["research"])
_IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")
_SCENARIO_META = {
    "scenario-auth-failure-v1": {
        "name": "Authentication Failure Pattern", "category": "IDENTITY",
        "description": (
            "Five synthetic failures followed by a success within the fixed rule window."
        ),
    },
    "scenario-auth-benign-control-v1": {
        "name": "Benign Control Sequence", "category": "CONTROL",
        "description": (
            "A registered synthetic control sequence with failures and no following success."
        ),
    },
}


def _require_mission(db: Session, workspace_id: str, mission_id: str) -> Mission:
    mission = db.scalar(select(Mission).where(
        Mission.id == mission_id, Mission.workspace_id == workspace_id,
    ))
    if mission is None:
        raise ApiError(404, "MISSION_NOT_FOUND", "The requested mission was not found.")
    return mission


def _require_run(db: Session, workspace_id: str, mission_id: str, run_id: str) -> SimulationRun:
    run = db.scalar(select(SimulationRun).where(
        SimulationRun.id == run_id, SimulationRun.workspace_id == workspace_id,
        SimulationRun.mission_id == mission_id,
    ))
    if run is None:
        raise ApiError(404, "SIMULATION_RUN_NOT_FOUND", "The requested run was not found.")
    return run


def _verification_public(item: OrigoVerification) -> VerificationPublic:
    return VerificationPublic(
        id=item.id, schema_version=item.schema_version, workspace_id=item.workspace_id,
        mission_id=item.mission_id, run_id=item.run_id, status=item.status,
        verifier_version=item.verifier_version, checks=item.checks, reasons=item.reasons,
        discrepancies=item.discrepancies, evidence_ids=item.evidence_ids,
        evidence_fingerprints=item.evidence_fingerprints,
        idempotency_key=item.idempotency_key, created_at=item.created_at,
    )


def _build_report(db: Session, workspace_id: str, mission: Mission) -> dict[str, object]:
    baseline = db.scalar(select(WorldSnapshot).where(
        WorldSnapshot.workspace_id == workspace_id, WorldSnapshot.mission_id == mission.id,
    ).order_by(WorldSnapshot.sequence.desc()).limit(1))
    runs = db.scalars(select(SimulationRun).where(
        SimulationRun.workspace_id == workspace_id, SimulationRun.mission_id == mission.id,
    ).order_by(SimulationRun.started_at.desc(), SimulationRun.id.desc()).limit(100)).all()
    evidence = db.scalars(select(EvidenceRecord).where(
        EvidenceRecord.workspace_id == workspace_id, EvidenceRecord.mission_id == mission.id,
    ).order_by(EvidenceRecord.created_at.asc(), EvidenceRecord.id.asc()).limit(1000)).all()
    verifications = db.scalars(select(OrigoVerification).where(
        OrigoVerification.workspace_id == workspace_id, OrigoVerification.mission_id == mission.id,
    ).order_by(OrigoVerification.created_at.desc(), OrigoVerification.id.desc()).limit(1000)).all()
    latest_by_run: dict[str, OrigoVerification] = {}
    for item in verifications:
        latest_by_run.setdefault(item.run_id, item)
    evidence_by_run: dict[str, list[EvidenceRecord]] = {}
    for item in evidence:
        evidence_by_run.setdefault(item.run_id, []).append(item)

    return {
        "report_type": "nexorion.mission-research-report",
        "report_schema_version": "1.0",
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "platform": "NEXORION",
        "environment": "SYNTHETIC (ISOLATED)",
        "scope": {
            "workspace_id": workspace_id, "mission_id": mission.id,
            "mission_objective": mission.objective, "mission_state": mission.state,
            "mission_version": mission.version, "mission_scope": mission.scope,
            "autonomy_tier": mission.autonomy_tier,
        },
        "baseline": None if baseline is None else {
            "id": baseline.id, "sequence": baseline.sequence, "graph_digest": baseline.graph_digest,
            "entity_count": len(baseline.snapshot.get("entities", [])),
            "relationship_count": len(baseline.snapshot.get("relationships", [])),
            "created_at": baseline.created_at.isoformat(),
        },
        "runs": [
            {
                "id": run.id, "scenario_id": run.scenario_id, "execution_status": run.status,
                "outcome": run.outcome, "started_at": run.started_at.isoformat(),
                "completed_at": run.completed_at.isoformat(), "baseline_id": run.baseline_id,
                "fixture_version": run.fixture_version, "rule_set_version": run.rule_set_version,
                "input_digest": run.input_digest, "output_digest": run.output_digest,
                "summary": run.result.get("summary") if isinstance(run.result, dict) else None,
                "supporting_event_ids": run.result.get("supporting_event_ids", [])
                    if isinstance(run.result, dict) else [],
                "evidence_ids": [item.id for item in evidence_by_run.get(run.id, [])],
                "origo_verification": None if run.id not in latest_by_run else {
                    "id": latest_by_run[run.id].id, "status": latest_by_run[run.id].status,
                    "verifier_version": latest_by_run[run.id].verifier_version,
                    "checks": latest_by_run[run.id].checks,
                    "reasons": latest_by_run[run.id].reasons,
                    "discrepancies": latest_by_run[run.id].discrepancies,
                    "created_at": latest_by_run[run.id].created_at.isoformat(),
                },
            } for run in runs
        ],
        "evidence": [
            {
                "id": item.id, "run_id": item.run_id, "evidence_type": item.evidence_type,
                "source_class": item.source_class, "source_ref": item.source_ref,
                "producer": item.producer, "producer_version": item.producer_version,
                "content_digest": item.content_digest, "payload": item.payload,
                "limitations": item.limitations, "created_at": item.created_at.isoformat(),
            } for item in evidence
        ],
        "verification_history": [
            {
                "id": item.id, "run_id": item.run_id, "status": item.status,
                "verifier_version": item.verifier_version, "checks": item.checks,
                "reasons": item.reasons, "discrepancies": item.discrepancies,
                "evidence_ids": item.evidence_ids,
                "evidence_fingerprints": item.evidence_fingerprints,
                "created_at": item.created_at.isoformat(),
            } for item in verifications
        ],
        "limitations": list(LIMITATIONS) + [
            "Only persisted synthetic research records are represented.",
            "Historical fixture-consistency fields are not Origo verification history.",
            "A missing verification record means verification was not requested "
            "or was not recorded.",
        ],
    }


def _markdown(report: dict[str, object]) -> str:
    scope = report["scope"]
    assert isinstance(scope, dict)
    lines = [
        "# NEXORION Synthetic Mission Research Report", "",
        f"- Report schema: {report['report_schema_version']}",
        f"- Generated at: {report['report_generated_at']}",
        f"- Environment: {report['environment']}",
        f"- Workspace ID: {scope['workspace_id']}", f"- Mission ID: {scope['mission_id']}",
        f"- Objective: {str(scope['mission_objective']).replace(chr(10), ' ')}",
        f"- Mission lifecycle: {scope['mission_state']}",
        f"- Autonomy tier: {scope['autonomy_tier']}", "", "## Baseline", "",
    ]
    baseline = report["baseline"]
    if not isinstance(baseline, dict):
        lines.append("No persisted baseline is available.")
    else:
        lines.extend([
            f"- Baseline ID: {baseline['id']}", f"- Sequence: {baseline['sequence']}",
            f"- Graph digest (SHA-256): {baseline['graph_digest']}",
            f"- Entities: {baseline['entity_count']}",
            f"- Relationships: {baseline['relationship_count']}",
            f"- Captured at: {baseline['created_at']}",
        ])
    lines.extend(["", "## Simulation runs", ""])
    runs = report["runs"]
    assert isinstance(runs, list)
    if not runs:
        lines.append("No persisted simulation runs are available.")
    for run in runs:
        verification = run["origo_verification"]
        verification_status = (
            verification["status"]
            if isinstance(verification, dict)
            else "not requested"
        )
        lines.extend([
            f"### Run {run['id']}", "", f"- Scenario: {run['scenario_id']}",
            f"- Execution status: {run['execution_status']}", f"- Outcome: {run['outcome']}",
            f"- Origo verification: {verification_status}", f"- Baseline: {run['baseline_id']}",
            f"- Input fingerprint: {run['input_digest']}",
            f"- Output fingerprint: {run['output_digest']}",
            f"- Summary: {str(run['summary'] or 'No persisted summary').replace(chr(10), ' ')}",
            "- Evidence references: "
            + (", ".join(run["evidence_ids"]) if run["evidence_ids"] else "none"),
        ])
        if isinstance(verification, dict):
            lines.extend(["", "Verification reasons:"])
            lines.extend(
                f"- {str(value).replace(chr(10), ' ')}"
                for value in verification["reasons"]
            )
            for discrepancy in verification["discrepancies"]:
                lines.append(f"- Discrepancy: {str(discrepancy)}")
        lines.append("")
    lines.extend(["## Evidence register", ""])
    evidence = report["evidence"]
    assert isinstance(evidence, list)
    if not evidence:
        lines.append("No persisted evidence is available.")
    for item in evidence:
        lines.extend([
            f"- ID: {item['id']} (run {item['run_id']})",
            f"  - Type: {item['evidence_type']}; source class: {item['source_class']}",
            f"  - Source reference: {item['source_ref']}",
            f"  - Producer: {item['producer']} {item['producer_version']}",
            f"  - SHA-256: {item['content_digest']}",
        ])
    lines.extend(["", "## Verification history", ""])
    history = report["verification_history"]
    assert isinstance(history, list)
    if not history:
        lines.append("No Origo verification attempts have been recorded.")
    for item in history:
        lines.append(
            f"- {item['created_at']} · run {item['run_id']} · {item['status']} · "
            f"verifier {item['verifier_version']}"
        )
        for reason in item["reasons"]:
            lines.append(f"  - {str(reason).replace(chr(10), ' ')}")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {str(item).replace(chr(10), ' ')}" for item in report["limitations"])
    return "\n".join(lines) + "\n"


@router.get("/scenarios")
def list_scenarios(user: User = Depends(get_current_user)) -> dict[str, object]:
    """Expose registered synthetic scenarios, not unregistered UI placeholders."""
    items = []
    for scenario_id, fixture in SCENARIO_REGISTRY.items():
        metadata = _SCENARIO_META.get(scenario_id, {})
        items.append({
            "id": scenario_id, "name": metadata.get("name", scenario_id),
            "category": metadata.get("category", "SYNTHETIC"),
            "description": metadata.get("description", "Registered synthetic scenario."),
            "enabled": True, "fixture_version": fixture["fixture_version"],
            "rule_set_version": RULE_SET_VERSION, "source_class": "synthetic",
            "limitations": list(LIMITATIONS),
        })
    return {"items": items, "catalog_version": "1.0"}


@router.post("/missions/{mission_id}/runs/{run_id}/verify",
             response_model=VerificationPublic, status_code=201)
def verify_run(
    mission_id: str, run_id: str, request: Request, response: Response,
    user: User = Depends(get_current_user), _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> VerificationPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    assert workspace_id is not None
    mission = _require_mission(db, workspace_id, mission_id)
    run = _require_run(db, workspace_id, mission.id, run_id)
    if idempotency_key is not None and not _IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
        raise ApiError(400, "IDEMPOTENCY_KEY_INVALID",
            "Idempotency-Key must contain 8 to 128 safe characters.")
    if idempotency_key:
        existing = db.scalar(select(OrigoVerification).where(
            OrigoVerification.workspace_id == workspace_id,
            OrigoVerification.run_id == run.id,
            OrigoVerification.idempotency_key == idempotency_key,
        ))
        if existing is not None:
            response.status_code = 200
            return _verification_public(existing)

    evidence = db.scalars(select(EvidenceRecord).where(
        EvidenceRecord.workspace_id == workspace_id, EvidenceRecord.mission_id == mission.id,
        EvidenceRecord.run_id == run.id,
    ).order_by(EvidenceRecord.created_at.asc(), EvidenceRecord.id.asc())).all()
    result = evaluate_persisted_run(run, evidence)
    attempt = OrigoVerification(
        id=new_id(), schema_version="1.0", workspace_id=workspace_id, mission_id=mission.id,
        run_id=run.id, status=str(result["status"]), verifier_version=ORIGO_VERIFIER_VERSION,
        checks=result["checks"], reasons=result["reasons"], discrepancies=result["discrepancies"],
        evidence_ids=result["evidence_ids"], evidence_fingerprints=result["evidence_fingerprints"],
        idempotency_key=idempotency_key,
    )
    db.add(attempt)
    db.add(AuditEvent(
        actor_id=user.id, workspace_id=workspace_id, action="verification.completed",
        resource_type="origo_verification", resource_id=attempt.id, decision="allow",
        reason="verification_" + str(result["status"]), request_id=request.state.request_id,
    ))
    # Only persisted Origo verification may establish a terminal mission outcome.
    verifier_commands = {
        "verified": "verified_success",
        "failed": "verification_failed",
        "disputed": "verification_disputed",
        "inconclusive": "verification_inconclusive",
    }
    if mission.state == "verifying":
        transition_mission(
            db, mission=mission, actor_id=None, actor_kind="origo-verifier",
            command=verifier_commands[str(result["status"])],
            expected_version=mission.version,
            reason="independent Origo verification: " + str(result["status"]),
            request_id=request.state.request_id, verifier_authorized=True,
        )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        if idempotency_key:
            existing = db.scalar(select(OrigoVerification).where(
                OrigoVerification.workspace_id == workspace_id,
                OrigoVerification.run_id == run.id,
                OrigoVerification.idempotency_key == idempotency_key,
            ))
            if existing is not None:
                response.status_code = 200
                return _verification_public(existing)
        raise ApiError(
            409,
            "VERIFICATION_CONFLICT",
            "The verification request conflicted with another operation; retry with a new key.",
        ) from exc
    db.refresh(attempt)
    return _verification_public(attempt)


@router.get("/missions/{mission_id}/runs/{run_id}/verification",
            response_model=VerificationHistoryPublic)
def verification_history(
    mission_id: str, run_id: str, user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> VerificationHistoryPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    assert workspace_id is not None
    mission = _require_mission(db, workspace_id, mission_id)
    _require_run(db, workspace_id, mission.id, run_id)
    rows = db.scalars(select(OrigoVerification).where(
        OrigoVerification.workspace_id == workspace_id, OrigoVerification.mission_id == mission.id,
        OrigoVerification.run_id == run_id,
    ).order_by(OrigoVerification.created_at.desc(), OrigoVerification.id.desc())).all()
    items = [_verification_public(item) for item in rows]
    return VerificationHistoryPublic(items=items, latest=items[0] if items else None)


@router.get("/missions/{mission_id}/report")
def mission_report(
    mission_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> dict[str, object]:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    assert workspace_id is not None
    return _build_report(db, workspace_id, _require_mission(db, workspace_id, mission_id))


@router.get("/missions/{mission_id}/report.md", response_class=PlainTextResponse)
def mission_report_markdown(
    mission_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> PlainTextResponse:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    assert workspace_id is not None
    mission = _require_mission(db, workspace_id, mission_id)
    return PlainTextResponse(
        _markdown(_build_report(db, workspace_id, mission)),
        media_type="text/markdown",
    )
