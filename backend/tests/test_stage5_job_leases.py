"""Lease and recovery invariants for durable synthetic jobs."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Mission, User, Workspace, WorkspaceMembership
from app.services.job_leases import claim_next_job, reconcile_expired_leases
from app.services.lifecycle import canonical_mission_digest
from app.stage5_models import MissionApproval, MissionJob, MissionJobAttempt


def _seed_job(db: Session) -> tuple[Mission, MissionJob]:
    user = User(email="lease-test@example.test", password_hash="test-hash")
    approver = User(email="lease-approver@example.test", password_hash="test-hash")
    workspace = Workspace(name="lease-test")
    db.add_all([user, approver, workspace])
    db.flush()
    db.add(WorkspaceMembership(user_id=user.id, workspace_id=workspace.id, role="owner"))
    mission = Mission(
        workspace_id=workspace.id, requester_id=user.id,
        objective="Test bounded synthetic job lease recovery",
        scope={"mode": "synthetic_only", "scenario_ids": ["scenario-auth-failure-v1"],
               "entity_ids": [], "excluded_targets": ["external systems"]},
        autonomy_tier="simulate_synthetic", state="queued", version=2,
    )
    db.add(mission)
    db.flush()
    now = datetime.now(timezone.utc)
    digest = canonical_mission_digest(mission)
    approval = MissionApproval(
        workspace_id=workspace.id, mission_id=mission.id, requester_id=user.id,
        approver_id=approver.id, action_class="synthetic_simulation", approved_scope=mission.scope,
        constraints={"synthetic_only": True}, plan_digest=digest, plan_version=1,
        decision="approved", decision_reason="test", created_at=now,
        expires_at=now + timedelta(minutes=10), consumed_at=now,
    )
    db.add(approval)
    db.flush()
    job = MissionJob(
        workspace_id=workspace.id, mission_id=mission.id, approval_id=approval.id,
        plan_digest=digest, plan_version=1, scenario_id="scenario-auth-failure-v1",
        idempotency_key="lease-test-key-001", status="queued", attempt_count=0,
        max_attempts=2, evidence_refs=[], created_at=now, updated_at=now,
    )
    db.add(job)
    db.flush()
    return mission, job


def test_claim_revalidates_and_records_attempt() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as db:
            mission, job = _seed_job(db)
            claimed = claim_next_job(db, worker_id="synthetic-worker-1", lease_seconds=10)
            assert claimed is not None
            assert claimed.id == job.id
            assert claimed.status == "running"
            assert claimed.lease_owner == "synthetic-worker-1"
            assert claimed.lease_expires_at is not None
            assert mission.state == "running"
            attempt = db.scalar(select(MissionJobAttempt).where(MissionJobAttempt.job_id == job.id))
            assert attempt is not None
            assert attempt.termination_confirmed is False
    finally:
        engine.dispose()


def test_expired_lease_becomes_uncertain_not_queued() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    try:
        with Session(engine, expire_on_commit=False) as db:
            mission, job = _seed_job(db)
            claimed = claim_next_job(db, worker_id="synthetic-worker-2", lease_seconds=10)
            assert claimed is not None
            claimed.lease_expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
            db.flush()
            changed = reconcile_expired_leases(db)
            assert changed == 1
            assert claimed.status == "uncertain"
            assert claimed.outcome == "lease_expired_termination_unconfirmed"
            assert claimed.status != "queued"
            assert mission.state == "failed"
            attempt = db.scalar(select(MissionJobAttempt).where(MissionJobAttempt.job_id == job.id))
            assert attempt is not None
            assert attempt.status == "uncertain"
            assert attempt.termination_confirmed is False
    finally:
        engine.dispose()
