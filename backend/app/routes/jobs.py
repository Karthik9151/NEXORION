"""Durable synthetic job submission and idempotent cancellation."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, Request
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_csrf, require_workspace_membership
from app.errors import ApiError
from app.models import AuditEvent, Mission, User, WorldSnapshot
from app.schemas import StrictModel
from app.services.lifecycle import canonical_mission_digest, transition_mission
from app.simulation import SCENARIO_REGISTRY
from app.stage5_models import MissionApproval, MissionJob

router = APIRouter(prefix="/missions", tags=["mission-jobs"])


class JobCreate(StrictModel):
    scenario_id: str = Field(min_length=1, max_length=100)
    idempotency_key: str = Field(min_length=8, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")


class JobPublic(StrictModel):
    id: str
    workspace_id: str
    mission_id: str
    approval_id: str | None
    plan_digest: str
    plan_version: int
    scenario_id: str
    idempotency_key: str
    status: str
    lease_owner: str | None
    lease_expires_at: datetime | None
    heartbeat_at: datetime | None
    cancel_requested_at: datetime | None
    attempt_count: int
    max_attempts: int
    outcome: str | None
    evidence_refs: list[str]
    created_at: datetime
    updated_at: datetime


def _public(job: MissionJob) -> JobPublic:
    return JobPublic(
        id=job.id, workspace_id=job.workspace_id, mission_id=job.mission_id,
        approval_id=job.approval_id, plan_digest=job.plan_digest,
        plan_version=job.plan_version, scenario_id=job.scenario_id,
        idempotency_key=job.idempotency_key, status=job.status,
        lease_owner=job.lease_owner, lease_expires_at=job.lease_expires_at,
        heartbeat_at=job.heartbeat_at, cancel_requested_at=job.cancel_requested_at,
        attempt_count=job.attempt_count, max_attempts=job.max_attempts,
        outcome=job.outcome, evidence_refs=job.evidence_refs,
        created_at=job.created_at, updated_at=job.updated_at,
    )


@router.post("/{mission_id}/jobs", response_model=JobPublic, status_code=201)
def enqueue_job(
    mission_id: str, payload: JobCreate, request: Request,
    user: User = Depends(get_current_user), _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> JobPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    mission = db.scalar(select(Mission).where(
        Mission.id == mission_id, Mission.workspace_id == workspace_id,
    ))
    if mission is None:
        raise ApiError(404, "MISSION_NOT_FOUND", "The requested mission was not found.")
    existing = db.scalar(select(MissionJob).where(
        MissionJob.workspace_id == workspace_id,
        MissionJob.mission_id == mission.id,
        MissionJob.idempotency_key == payload.idempotency_key,
    ))
    if existing is not None:
        if existing.scenario_id != payload.scenario_id:
            raise ApiError(409, "IDEMPOTENCY_KEY_REUSED", "This idempotency key belongs to a different scenario.")
        return _public(existing)
    if mission.state != "planned":
        raise ApiError(409, "MISSION_NOT_PLANNED", "Only a planned mission can be queued.")
    active_job = db.scalar(select(MissionJob.id).where(
        MissionJob.workspace_id == workspace_id, MissionJob.mission_id == mission.id,
        MissionJob.status.in_(["queued", "claimed", "running", "cancelling", "uncertain", "review_required"]),
    ))
    if active_job is not None:
        raise ApiError(409, "MISSION_JOB_ALREADY_ACTIVE", "A mission may have only one active or uncertain job.")
    if mission.autonomy_tier != "simulate_synthetic" or mission.scope.get("mode") != "synthetic_only":
        raise ApiError(403, "SYNTHETIC_SCOPE_REQUIRED", "Only explicitly synthetic missions may be queued.")
    if payload.scenario_id not in mission.scope.get("scenario_ids", []) or payload.scenario_id not in SCENARIO_REGISTRY:
        raise ApiError(403, "SCENARIO_OUT_OF_SCOPE", "The scenario must be registered and included in mission scope.")
    baseline = db.scalar(select(WorldSnapshot).where(
        WorldSnapshot.workspace_id == workspace_id, WorldSnapshot.mission_id == mission.id,
    ).order_by(WorldSnapshot.sequence.desc()).limit(1))
    if baseline is None:
        raise ApiError(409, "BASELINE_REQUIRED", "Capture a baseline before queueing synthetic work.")
    now = datetime.now(timezone.utc)
    digest = canonical_mission_digest(mission)
    approvals = db.scalars(select(MissionApproval).where(
        MissionApproval.workspace_id == workspace_id,
        MissionApproval.mission_id == mission.id,
        MissionApproval.action_class == "synthetic_simulation",
        MissionApproval.decision == "approved",
        MissionApproval.plan_digest == digest,
        MissionApproval.plan_version == mission.version,
        MissionApproval.revoked_at.is_(None),
        MissionApproval.invalidated_at.is_(None),
        MissionApproval.consumed_at.is_(None),
        MissionApproval.expires_at > now,
    )).all()
    denied = db.scalar(select(MissionApproval.id).where(
        MissionApproval.workspace_id == workspace_id,
        MissionApproval.mission_id == mission.id,
        MissionApproval.plan_version == mission.version,
        MissionApproval.decision == "denied",
        MissionApproval.revoked_at.is_(None),
        MissionApproval.invalidated_at.is_(None),
    ))
    if denied is not None:
        raise ApiError(403, "APPROVAL_DENIED", "A current approval denial blocks queueing.")
    approvals = [item for item in approvals if item.approved_scope == mission.scope]
    if len(approvals) != 1:
        raise ApiError(409, "APPROVAL_REQUIRED", "Exactly one current, unconsumed approval must match the mission contract.")
    approval = approvals[0]
    try:
        transition_mission(
            db, mission=mission, actor_id=user.id, actor_kind="user",
            command="queue", expected_version=mission.version,
            reason="approved synthetic job queued", request_id=request.state.request_id,
        )
        job = MissionJob(
            workspace_id=workspace_id, mission_id=mission.id, approval_id=approval.id,
            plan_digest=digest, plan_version=mission.version - 1,
            scenario_id=payload.scenario_id, idempotency_key=payload.idempotency_key,
            status="queued", attempt_count=0, max_attempts=2, evidence_refs=[],
            created_at=now, updated_at=now,
        )
        db.add(job)
        db.flush()
        db.add(AuditEvent(
            actor_id=user.id, workspace_id=workspace_id, action="mission.job_queued",
            resource_type="mission_job", resource_id=job.id, decision="allow",
            reason="registered_synthetic_scenario", request_id=request.state.request_id,
        ))
        db.commit()
        db.refresh(job)
        return _public(job)
    except ApiError as exc:
        db.rollback()
        existing = db.scalar(select(MissionJob).where(
            MissionJob.workspace_id == workspace_id, MissionJob.mission_id == mission.id,
            MissionJob.idempotency_key == payload.idempotency_key,
        ))
        if existing is not None and existing.scenario_id == payload.scenario_id:
            return _public(existing)
        raise exc
    except IntegrityError as exc:
        db.rollback()
        # A concurrent identical request may have won the unique-key race.
        existing = db.scalar(select(MissionJob).where(
            MissionJob.workspace_id == workspace_id, MissionJob.mission_id == mission.id,
            MissionJob.idempotency_key == payload.idempotency_key,
        ))
        if existing is not None and existing.scenario_id == payload.scenario_id:
            return _public(existing)
        raise ApiError(409, "JOB_CONFLICT", "A concurrent queue operation conflicted; reload the mission.") from exc
    except Exception:
        db.rollback()
        raise


@router.post("/{mission_id}/jobs/{job_id}/cancel", response_model=JobPublic)
def cancel_job(
    mission_id: str, job_id: str, request: Request,
    user: User = Depends(get_current_user), _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> JobPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    job = db.scalar(select(MissionJob).where(
        MissionJob.id == job_id, MissionJob.mission_id == mission_id,
        MissionJob.workspace_id == workspace_id,
    ))
    if job is None:
        raise ApiError(404, "JOB_NOT_FOUND", "The requested job was not found.")
    now = datetime.now(timezone.utc)
    if job.status in {"cancelled", "succeeded", "failed"}:
        return _public(job)
    mission = db.scalar(select(Mission).where(
        Mission.id == mission_id, Mission.workspace_id == workspace_id,
    ))
    if mission is None:
        raise ApiError(404, "MISSION_NOT_FOUND", "The requested mission was not found.")
    if job.status == "queued":
        job.status = "cancelled"
        job.outcome = "cancelled_before_start"
        if mission.state == "queued":
            transition_mission(
                db, mission=mission, actor_id=user.id, actor_kind="user",
                command="cancel_before_start", expected_version=mission.version,
                reason="queued job cancelled before dispatch", request_id=request.state.request_id,
            )
    else:
        job.cancel_requested_at = job.cancel_requested_at or now
        job.status = "cancelling"
        if mission.state == "running":
            transition_mission(
                db, mission=mission, actor_id=user.id, actor_kind="user",
                command="cancel", expected_version=mission.version,
                reason="cancellation requested; worker termination pending",
                request_id=request.state.request_id,
            )
    job.updated_at = now
    db.add(AuditEvent(
        actor_id=user.id, workspace_id=workspace_id, action="mission.job_cancellation",
        resource_type="mission_job", resource_id=job.id, decision="allow",
        reason="idempotent_cancellation_request", request_id=request.state.request_id,
    ))
    db.commit()
    db.refresh(job)
    return _public(job)


@router.get("/{mission_id}/jobs", response_model=list[JobPublic])
def list_jobs(
    mission_id: str, user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> list[JobPublic]:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    mission = db.scalar(select(Mission.id).where(
        Mission.id == mission_id, Mission.workspace_id == workspace_id,
    ))
    if mission is None:
        raise ApiError(404, "MISSION_NOT_FOUND", "The requested mission was not found.")
    rows = db.scalars(select(MissionJob).where(
        MissionJob.workspace_id == workspace_id, MissionJob.mission_id == mission_id,
    ).order_by(MissionJob.created_at.asc())).all()
    return [_public(row) for row in rows]
