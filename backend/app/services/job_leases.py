"""PostgreSQL-backed lease operations for registered synthetic jobs.

No broker or external worker platform is introduced. Lease expiry is treated
as uncertainty, never as proof that a prior worker stopped.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import AuditEvent, Mission
from app.services.lifecycle import canonical_mission_digest, transition_mission
from app.stage5_models import MissionApproval, MissionJob, MissionJobAttempt
from app.simulation import SCENARIO_REGISTRY


def _now() -> datetime:
    return datetime.now(timezone.utc)


def claim_next_job(
    db: Session, *, worker_id: str, lease_seconds: int = 30, job_id: str | None = None,
) -> MissionJob | None:
    if not worker_id.strip() or len(worker_id) > 128 or not 5 <= lease_seconds <= 120:
        raise ApiError(422, "INVALID_WORKER_LEASE", "Worker identity or lease duration is invalid.")
    statement = select(MissionJob).where(MissionJob.status == "queued")
    if job_id is not None:
        statement = statement.where(MissionJob.id == job_id)
    job = db.scalar(
        statement.order_by(MissionJob.created_at.asc(), MissionJob.id.asc())
        .with_for_update(skip_locked=True).limit(1)
    )
    if job is None:
        return None
    now = _now()
    mission = db.scalar(select(Mission).where(
        Mission.id == job.mission_id, Mission.workspace_id == job.workspace_id,
    ))
    approval = db.scalar(select(MissionApproval).where(
        MissionApproval.id == job.approval_id,
        MissionApproval.workspace_id == job.workspace_id,
        MissionApproval.mission_id == job.mission_id,
    )) if job.approval_id else None
    approval_expiry = None if approval is None else approval.expires_at
    if approval_expiry is not None and approval_expiry.tzinfo is None:
        approval_expiry = approval_expiry.replace(tzinfo=timezone.utc)
    valid = (
        mission is not None and mission.state == "queued"
        and mission.autonomy_tier == "simulate_synthetic"
        and mission.scope.get("mode") == "synthetic_only"
        and job.scenario_id in mission.scope.get("scenario_ids", [])
        and job.scenario_id in SCENARIO_REGISTRY
        and canonical_mission_digest(mission) == job.plan_digest
        and mission.version == job.plan_version + 1
        and approval is not None and approval.decision == "approved"
        and approval.plan_digest == job.plan_digest
        and approval.plan_version == job.plan_version
        and approval.approved_scope == mission.scope
        and approval_expiry is not None and approval_expiry > now
        and approval.revoked_at is None and approval.invalidated_at is None
        and approval.consumed_at is not None
    )
    if not valid:
        job.status = "review_required"
        job.outcome = "authorization_or_plan_revalidation_failed"
        job.updated_at = now
        db.add(AuditEvent(
            actor_id=None, workspace_id=job.workspace_id, action="mission.job_recovery_blocked",
            resource_type="mission_job", resource_id=job.id, decision="deny",
            reason="approval_scope_plan_or_mission_state_revalidation_failed",
            request_id=f"worker:{worker_id}",
        ))
        db.flush()
        return None
    active_attempt = db.scalar(select(MissionJobAttempt.id).where(
        MissionJobAttempt.job_id == job.id,
        MissionJobAttempt.status.in_(["claimed", "running", "cancelling", "uncertain"]),
        MissionJobAttempt.termination_confirmed.is_(False),
    ))
    if active_attempt is not None:
        job.status = "uncertain"
        job.outcome = "prior_attempt_may_still_be_running"
        job.updated_at = now
        db.flush()
        return None
    transition_mission(
        db, mission=mission, actor_id=None, actor_kind="worker",
        command="start", expected_version=mission.version,
        reason="worker claimed approved synthetic job", request_id=f"worker:{worker_id}",
    )
    job.status = "running"
    job.lease_owner = worker_id
    job.lease_expires_at = now + timedelta(seconds=lease_seconds)
    job.heartbeat_at = now
    job.attempt_count += 1
    job.updated_at = now
    db.add(MissionJobAttempt(
        workspace_id=job.workspace_id, mission_id=job.mission_id, job_id=job.id,
        attempt_number=job.attempt_count, worker_id=worker_id, status="running",
        started_at=now, heartbeat_at=now, evidence_refs=[], termination_confirmed=False,
    ))
    db.add(AuditEvent(
        actor_id=None, workspace_id=job.workspace_id, action="mission.job_claimed",
        resource_type="mission_job", resource_id=job.id, decision="allow",
        reason="atomic_postgresql_lease_claim", request_id=f"worker:{worker_id}",
    ))
    db.flush()
    return job


def heartbeat_job(db: Session, *, job_id: str, worker_id: str, lease_seconds: int = 30) -> MissionJob:
    now = _now()
    job = db.scalar(select(MissionJob).where(MissionJob.id == job_id).with_for_update())
    if job is None:
        raise ApiError(404, "JOB_NOT_FOUND", "The requested job was not found.")
    if job.lease_owner != worker_id or job.status != "running":
        raise ApiError(409, "LEASE_NOT_OWNED", "This worker does not hold the active job lease.")
    if job.cancel_requested_at is not None:
        raise ApiError(409, "CANCELLATION_REQUESTED", "The worker must stop and confirm termination.")
    if not 5 <= lease_seconds <= 120:
        raise ApiError(422, "INVALID_WORKER_LEASE", "Lease duration must be between 5 and 120 seconds.")
    job.heartbeat_at = now
    job.lease_expires_at = now + timedelta(seconds=lease_seconds)
    job.updated_at = now
    attempt = db.scalar(select(MissionJobAttempt).where(
        MissionJobAttempt.job_id == job.id,
        MissionJobAttempt.attempt_number == job.attempt_count,
    ))
    if attempt is not None:
        attempt.heartbeat_at = now
    db.add(AuditEvent(
        actor_id=None, workspace_id=job.workspace_id, action="mission.job_heartbeat",
        resource_type="mission_job", resource_id=job.id, decision="allow",
        reason="worker_lease_renewed", request_id=f"worker:{worker_id}",
    ))
    db.flush()
    return job


def reconcile_expired_leases(db: Session) -> int:
    """Mark expired running leases uncertain; never reassign based on timeout alone."""
    now = _now()
    jobs = db.scalars(select(MissionJob).where(
        MissionJob.status.in_(["running", "cancelling"]),
        MissionJob.lease_expires_at.is_not(None),
        MissionJob.lease_expires_at < now,
    ).with_for_update(skip_locked=True)).all()
    count = 0
    for job in jobs:
        job.status = "uncertain"
        job.outcome = "lease_expired_termination_unconfirmed"
        job.updated_at = now
        attempt = db.scalar(select(MissionJobAttempt).where(
            MissionJobAttempt.job_id == job.id,
            MissionJobAttempt.attempt_number == job.attempt_count,
        ))
        if attempt is not None:
            attempt.status = "uncertain"
            attempt.error_category = "lease_expired"
            # Deliberately keep termination_confirmed false.
        mission = db.scalar(select(Mission).where(
            Mission.id == job.mission_id, Mission.workspace_id == job.workspace_id,
        ))
        if mission is not None and mission.state in {"running", "cancelling"}:
            try:
                transition_mission(
                    db, mission=mission, actor_id=None, actor_kind="recovery",
                    command="fail", expected_version=mission.version,
                    reason="lease expired and safe worker termination cannot be established",
                    request_id="worker:recovery",
                )
            except ApiError:
                # Preserve the uncertain job and audit; never infer a safe replay.
                db.rollback()
        db.add(AuditEvent(
            actor_id=None, workspace_id=job.workspace_id, action="mission.job_lease_expired",
            resource_type="mission_job", resource_id=job.id, decision="deny",
            reason="worker_termination_unconfirmed_no_reassignment",
            request_id="worker:recovery",
        ))
        count += 1
    db.flush()
    return count


def confirm_job_stopped(
    db: Session, *, job_id: str, worker_id: str, evidence_refs: list[str] | None = None,
) -> MissionJob:
    """Persist an explicit worker stop acknowledgement; lease timeout is not an acknowledgement."""
    job = db.scalar(select(MissionJob).where(MissionJob.id == job_id).with_for_update())
    if job is None:
        raise ApiError(404, "JOB_NOT_FOUND", "The requested job was not found.")
    if job.lease_owner != worker_id or job.status != "cancelling" or job.cancel_requested_at is None:
        raise ApiError(409, "STOP_ACKNOWLEDGEMENT_NOT_EXPECTED", "This worker does not own a cancellation-requested job.")
    now = _now()
    attempt = db.scalar(select(MissionJobAttempt).where(
        MissionJobAttempt.job_id == job.id,
        MissionJobAttempt.attempt_number == job.attempt_count,
    ).with_for_update())
    if attempt is None:
        raise ApiError(409, "ATTEMPT_RECORD_MISSING", "Cannot establish safe termination without an attempt record.")
    attempt.status = "cancelled"
    attempt.ended_at = now
    attempt.termination_confirmed = True
    if evidence_refs:
        attempt.evidence_refs = list(dict.fromkeys([*attempt.evidence_refs, *evidence_refs]))[:100]
        job.evidence_refs = list(dict.fromkeys([*job.evidence_refs, *evidence_refs]))[:100]
    job.status = "cancelled"
    job.outcome = "worker_stop_acknowledged"
    job.lease_owner = None
    job.lease_expires_at = None
    job.updated_at = now
    mission = db.scalar(select(Mission).where(
        Mission.id == job.mission_id, Mission.workspace_id == job.workspace_id,
    ).with_for_update())
    if mission is not None and mission.state == "cancelling":
        transition_mission(
            db, mission=mission, actor_id=None, actor_kind="worker",
            command="cancelled", expected_version=mission.version,
            reason="worker explicitly confirmed safe termination",
            request_id=f"worker:{worker_id}",
        )
    db.add(AuditEvent(
        actor_id=None, workspace_id=job.workspace_id, action="mission.job_termination_confirmed",
        resource_type="mission_job", resource_id=job.id, decision="allow",
        reason="worker_stop_acknowledged", request_id=f"worker:{worker_id}",
    ))
    db.flush()
    return job
