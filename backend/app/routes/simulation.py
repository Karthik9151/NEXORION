"""Authorized, idempotent execution of fixed synthetic scenarios only."""

import re

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_csrf, require_workspace_membership
from app.errors import ApiError
from app.models import (
    AuditEvent,
    EvidenceRecord,
    Mission,
    SimulationRun,
    User,
    WorldSnapshot,
    new_id,
    utcnow,
)
from app.schemas import (
    EvidencePublic,
    SimulationRunCreate,
    SimulationRunPublic,
)
from app.services.job_leases import claim_next_job
from app.services.lifecycle import transition_mission
from app.stage5_models import MissionJob, MissionJobAttempt
from app.simulation import (
    LIMITATIONS,
    RULE_SET_VERSION,
    SCENARIO_REGISTRY,
    SIMULATOR_VERSION,
    digest,
    evaluate_fixture,
    get_fixture,
    verify_fixture_result,
)

router = APIRouter(tags=["simulation"])
_IDEMPOTENCY_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{8,128}$")


def _evidence_public(item: EvidenceRecord) -> EvidencePublic:
    return EvidencePublic(
        id=item.id,
        schema_version=item.schema_version,
        workspace_id=item.workspace_id,
        mission_id=item.mission_id,
        run_id=item.run_id,
        evidence_type=item.evidence_type,
        source_class="synthetic",
        source_ref=item.source_ref,
        producer=item.producer,
        producer_version=item.producer_version,
        content_digest=item.content_digest,
        payload=item.payload,
        limitations=item.limitations,
        created_at=item.created_at,
    )


def _run_public(db: Session, run: SimulationRun) -> SimulationRunPublic:
    evidence = db.scalars(
        select(EvidenceRecord)
        .where(EvidenceRecord.run_id == run.id, EvidenceRecord.workspace_id == run.workspace_id)
        .order_by(EvidenceRecord.created_at.asc(), EvidenceRecord.id.asc())
    ).all()
    return SimulationRunPublic(
        id=run.id,
        schema_version=run.schema_version,
        workspace_id=run.workspace_id,
        mission_id=run.mission_id,
        baseline_id=run.baseline_id,
        scenario_id=run.scenario_id,
        fixture_version=run.fixture_version,
        rule_set_version=run.rule_set_version,
        input_digest=run.input_digest,
        output_digest=run.output_digest,
        outcome=run.outcome,
        status="completed",
        result=run.result,
        evidence=[_evidence_public(item) for item in evidence],
        started_at=run.started_at,
        completed_at=run.completed_at,
    )


def _require_mission(db: Session, workspace_id: str, mission_id: str) -> Mission:
    mission = db.scalar(
        select(Mission).where(Mission.id == mission_id, Mission.workspace_id == workspace_id)
    )
    if mission is None:
        raise ApiError(404, "MISSION_NOT_FOUND", "The requested mission was not found.")
    return mission


def _audit_transition(
    request: Request,
    user: User,
    mission: Mission,
    old_state: str,
    new_state: str,
) -> AuditEvent:
    return AuditEvent(
        actor_id=user.id,
        workspace_id=mission.workspace_id,
        action="mission.state_transition",
        resource_type="mission",
        resource_id=mission.id,
        decision="allow",
        reason=f"{old_state}_to_{new_state}_synthetic_run",
        request_id=request.state.request_id,
    )


@router.post(
    "/missions/{mission_id}/simulate",
    response_model=SimulationRunPublic,
    status_code=201,
)
def simulate_mission(
    mission_id: str,
    payload: SimulationRunCreate,
    request: Request,
    user: User = Depends(get_current_user),
    _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
) -> SimulationRunPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    mission = _require_mission(db, workspace_id, mission_id)

    if not idempotency_key or not _IDEMPOTENCY_PATTERN.fullmatch(idempotency_key):
        raise ApiError(
            400,
            "IDEMPOTENCY_KEY_REQUIRED",
            "Provide an Idempotency-Key containing 8 to 128 safe characters.",
        )

    existing = db.scalar(
        select(SimulationRun).where(
            SimulationRun.workspace_id == workspace_id,
            SimulationRun.mission_id == mission.id,
            SimulationRun.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        if existing.scenario_id != payload.scenario_id:
            raise ApiError(
                409,
                "IDEMPOTENCY_KEY_REUSED",
                "The idempotency key was already used for a different scenario.",
            )
        return _run_public(db, existing)

    if mission.autonomy_tier != "simulate_synthetic":
        raise ApiError(
            403,
            "SIMULATION_TIER_REQUIRED",
            "The mission must explicitly request the simulate_synthetic autonomy tier.",
        )
    if mission.scope.get("mode") != "synthetic_only":
        raise ApiError(403, "SYNTHETIC_SCOPE_REQUIRED",
            "Only synthetic-only missions can run here.")
    if payload.scenario_id not in mission.scope.get("scenario_ids", []):
        raise ApiError(
            403,
            "SCENARIO_OUT_OF_SCOPE",
            "The requested scenario is not included in the mission scope.",
        )
    fixture = get_fixture(payload.scenario_id)
    if fixture is None or payload.scenario_id not in SCENARIO_REGISTRY:
        raise ApiError(404, "SCENARIO_NOT_FOUND",
            "The requested fixed synthetic scenario was not found.")

    baseline = db.scalar(
        select(WorldSnapshot)
        .where(WorldSnapshot.workspace_id == workspace_id, WorldSnapshot.mission_id == mission.id)
        .order_by(WorldSnapshot.sequence.desc())
        .limit(1)
    )
    if baseline is None:
        raise ApiError(409, "BASELINE_REQUIRED",
            "Capture a versioned world baseline before simulation.")
    if digest(baseline.snapshot) != baseline.graph_digest:
        raise ApiError(
            409,
            "BASELINE_INTEGRITY_CHECK_FAILED",
            "The stored baseline digest did not match its snapshot; execution was blocked.",
        )

    if mission.state != "queued":
        raise ApiError(
            409,
            "DURABLE_JOB_REQUIRED",
            "Direct simulation is disabled. Queue a planned mission with a current approval first.",
        )
    job = db.scalar(select(MissionJob).where(
        MissionJob.workspace_id == workspace_id,
        MissionJob.mission_id == mission.id,
        MissionJob.idempotency_key == idempotency_key,
        MissionJob.scenario_id == payload.scenario_id,
        MissionJob.status == "queued",
    ))
    if job is None:
        raise ApiError(409, "DURABLE_JOB_REQUIRED", "No matching queued job exists for this scenario and idempotency key.")
    claimed_job = claim_next_job(
        db, worker_id=f"synthetic-api-worker:{user.id}", lease_seconds=60, job_id=job.id,
    )
    if claimed_job is None:
        raise ApiError(409, "JOB_CLAIM_BLOCKED", "The job failed execution-boundary revalidation and requires review.")
    # Commit the lease and running state before work begins so recovery can observe it.
    # If the process dies during deterministic evaluation, the job remains running
    # until reconciliation marks the outcome uncertain; it is never silently replayed.
    db.commit()
    db.refresh(mission)
    db.refresh(claimed_job)
    started_at = utcnow()
    analysis = evaluate_fixture(payload.scenario_id, fixture)
    # This bounded fixture consistency check is not an Origo verification attempt.
    fixture_consistency = verify_fixture_result(payload.scenario_id, fixture, analysis)
    result = {
        **analysis,
        "fixture_consistency": fixture_consistency,
        "simulator_version": SIMULATOR_VERSION,
        "capabilities_used": ["read_registered_synthetic_fixture",
            "deterministic_rule_evaluation", "record_synthetic_evidence"],
        "capabilities_not_available": ["external_network", "host_commands",
            "real_credentials", "live_system_mutation"],
    }
    input_digest = digest(
        {
            "scenario_id": payload.scenario_id,
            "fixture_version": fixture["fixture_version"],
            "rule_set_version": RULE_SET_VERSION,
            "events": fixture["events"],
        }
    )
    output_digest = digest(result)
    run_id = new_id()
    source_ref = fixture["source_ref"]
    evidence_payload = {
        "payload_schema_version": "1.0",
        "scenario_id": payload.scenario_id,
        "fixture_version": fixture["fixture_version"],
        "outcome": analysis["outcome"],
        "supporting_event_ids": analysis["supporting_event_ids"],
        "event_count": analysis["event_count"],
        "rule_set_version": RULE_SET_VERSION,
        # Persist event detail so Origo can evaluate evidence without reloading the fixture.
        "events": fixture["events"],
    }
    evidence_record = EvidenceRecord(
        id=new_id(),
        workspace_id=workspace_id,
        mission_id=mission.id,
        run_id=run_id,
        evidence_type="synthetic_auth_event_cluster",
        source_class="synthetic",
        source_ref=source_ref,
        producer="nexorion-synthetic-simulator",
        producer_version=SIMULATOR_VERSION,
        content_digest=digest(evidence_payload),
        payload=evidence_payload,
        limitations=list(LIMITATIONS),
    )
    completed_at = utcnow()
    run = SimulationRun(
        id=run_id,
        workspace_id=workspace_id,
        mission_id=mission.id,
        baseline_id=baseline.id,
        scenario_id=payload.scenario_id,
        fixture_version=fixture["fixture_version"],
        rule_set_version=RULE_SET_VERSION,
        idempotency_key=idempotency_key,
        input_digest=input_digest,
        output_digest=output_digest,
        outcome=analysis["outcome"],
        status="completed",
        result=result,
        started_at=started_at,
        completed_at=completed_at,
    )
    db.add(run)
    db.flush()
    db.add(evidence_record)

    # Simulation completion is not an Origo verdict. Keep the mission in
    # verifying until the independent verification route records its outcome.
    transition_mission(
        db, mission=mission, actor_id=None, actor_kind="synthetic-worker",
        command="begin_verification", expected_version=mission.version,
        reason="registered deterministic scenario execution completed",
        request_id=request.state.request_id,
    )
    claimed_job.status = "succeeded"
    claimed_job.outcome = "simulation_completed_pending_origo"
    claimed_job.lease_owner = None
    claimed_job.lease_expires_at = None
    claimed_job.updated_at = completed_at
    attempt = db.scalar(select(MissionJobAttempt).where(
        MissionJobAttempt.job_id == claimed_job.id,
        MissionJobAttempt.attempt_number == claimed_job.attempt_count,
    ))
    if attempt is not None:
        attempt.status = "completed"
        attempt.ended_at = completed_at
        attempt.termination_confirmed = True
        attempt.evidence_refs = [evidence_record.id]
    claimed_job.evidence_refs = [evidence_record.id]
    db.add(AuditEvent(
        actor_id=None, workspace_id=workspace_id, action="mission.job_execution_completed",
        resource_type="mission_job", resource_id=claimed_job.id, decision="allow",
        reason="deterministic_synthetic_execution_finished_verification_pending",
        request_id=request.state.request_id,
    ))
    db.add(
        AuditEvent(
            actor_id=user.id,
            workspace_id=workspace_id,
            action="simulation.completed",
            resource_type="simulation_run",
            resource_id=run.id,
            decision="allow",
            reason="fixed_synthetic_scenario_completed_verification_pending",
            request_id=request.state.request_id,
        )
    )
    db.commit()
    db.refresh(run)
    db.refresh(mission)
    return _run_public(db, run)


@router.get("/missions/{mission_id}/runs", response_model=list[SimulationRunPublic])
def list_mission_runs(
    mission_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
) -> list[SimulationRunPublic]:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    _require_mission(db, workspace_id, mission_id)
    rows = db.scalars(
        select(SimulationRun)
        .where(SimulationRun.workspace_id == workspace_id, SimulationRun.mission_id == mission_id)
        .order_by(SimulationRun.started_at.desc(), SimulationRun.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [_run_public(db, item) for item in rows]
