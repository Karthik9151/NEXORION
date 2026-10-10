"""Authorized, idempotent execution of fixed synthetic scenarios only."""

import re
import time

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_csrf, require_workspace_membership
from app.errors import ApiError
from app.models import (
    EvidenceRecord,
    Mission,
    SimulationRun,
    User,
    WorldSnapshot,
)
from app.schemas import (
    EvidencePublic,
    SimulationRunCreate,
    SimulationRunPublic,
)
from app.services.job_leases import claim_next_job
from app.services.synthetic_worker import execute_claimed_job
from app.simulation import (
    SCENARIO_REGISTRY,
    digest,
    get_fixture,
)
from app.stage5_models import MissionJob

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

    # The durable queue is authoritative. A production in-process worker may
    # have claimed the job before this compatibility endpoint is called.
    job = db.scalar(select(MissionJob).where(
        MissionJob.workspace_id == workspace_id,
        MissionJob.mission_id == mission.id,
        MissionJob.idempotency_key == idempotency_key,
        MissionJob.scenario_id == payload.scenario_id,
    ))
    if job is None:
        raise ApiError(409, "DURABLE_JOB_REQUIRED",
            "No matching durable job exists for this scenario and idempotency key.")

    worker_enabled = bool(getattr(request.app.state, "worker_enabled", False))
    if job.status == "queued" and not worker_enabled:
        # Local tests/development can use the exact worker service synchronously
        # when the periodic worker is intentionally disabled.
        worker_id = f"synthetic-api-worker:{user.id}"
        claimed_job = claim_next_job(
            db, worker_id=worker_id, lease_seconds=60, job_id=job.id,
        )
        db.commit()  # Persist the lease before any fixture evaluation starts.
        if claimed_job is not None:
            execute_claimed_job(
                db, job_id=job.id, worker_id=worker_id,
                request_id=request.state.request_id,
            )
    # In production the background worker processes the queued record. Poll only
    # persisted state; never label a queued/running job as a completed run.
    deadline = time.monotonic() + 12.0
    while time.monotonic() < deadline:
        db.expire_all()
        existing = db.scalar(select(SimulationRun).where(
            SimulationRun.workspace_id == workspace_id,
            SimulationRun.mission_id == mission.id,
            SimulationRun.idempotency_key == idempotency_key,
        ))
        if existing is not None:
            if existing.scenario_id != payload.scenario_id:
                raise ApiError(409, "IDEMPOTENCY_KEY_REUSED",
                    "The idempotency key was already used for a different scenario.")
            return _run_public(db, existing)

        current_job = db.scalar(select(MissionJob).where(
            MissionJob.id == job.id,
            MissionJob.workspace_id == workspace_id,
            MissionJob.mission_id == mission.id,
        ))
        if current_job is None:
            raise ApiError(404, "JOB_NOT_FOUND", "The queued job no longer exists.")
        if current_job.status in {"review_required", "uncertain", "failed", "cancelled"}:
            raise ApiError(
                409, "JOB_REQUIRES_REVIEW",
                "The durable job did not complete. Review its persisted state "
                "before taking further action.",
            )
        if current_job.status == "succeeded":
            raise ApiError(409, "JOB_RESULT_MISSING",
                "The job is marked succeeded but no persisted run was found; execution is blocked.")
        time.sleep(0.1)

    raise ApiError(
        409, "JOB_STILL_RUNNING",
        "The durable job has not completed yet. Retry the same request "
        "with the same idempotency key.",
        retryable=True,
    )


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
