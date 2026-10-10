"""Stage 5 durable governance, lifecycle and worker records.

Imported by app.models so Alembic metadata includes these tables without
duplicating the existing Stage 2-4 entities.
"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


class MissionTransitionEvent(Base):
    __tablename__ = "mission_transition_events"
    __table_args__ = (
        Index("ix_mission_transition_workspace_mission", "workspace_id", "mission_id",
            "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="RESTRICT"),
        nullable=False)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True)
    actor_kind: Mapped[str] = mapped_column(String(24), nullable=False, default="user")
    old_state: Mapped[str] = mapped_column(String(32), nullable=False)
    new_state: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    object_version: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column("metadata", JSON, nullable=False,
        default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=_utcnow)


class MissionPlan(Base):
    """Append-only typed execution contract consumed by approvals and jobs."""

    __tablename__ = "mission_plans"
    __table_args__ = (
        UniqueConstraint(
            "workspace_id", "mission_id", "plan_version",
            name="uq_mission_plan_version",
        ),
        Index("ix_mission_plan_workspace_mission", "workspace_id", "mission_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False
    )
    mission_id: Mapped[str] = mapped_column(
        ForeignKey("missions.id", ondelete="RESTRICT"), nullable=False
    )
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    plan_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_document: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    created_by: Mapped[str] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow
    )


class MissionApproval(Base):
    __tablename__ = "mission_approvals"
    __table_args__ = (
        Index("ix_mission_approval_workspace_mission", "workspace_id", "mission_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="RESTRICT"),
        nullable=False)
    plan_id: Mapped[str | None] = mapped_column(
        ForeignKey("mission_plans.id", ondelete="RESTRICT"), nullable=True
    )
    requester_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False)
    approver_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True)
    action_class: Mapped[str] = mapped_column(String(64), nullable=False)
    approved_scope: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    constraints: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    plan_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False)
    decision: Mapped[str] = mapped_column(String(24), nullable=False)
    decision_reason: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=_utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    invalidated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MissionJob(Base):
    __tablename__ = "mission_jobs"
    __table_args__ = (
        UniqueConstraint("workspace_id", "mission_id", "idempotency_key",
            name="uq_mission_job_idempotency"),
        Index("ix_mission_job_claim", "status", "created_at"),
        Index("ix_mission_job_workspace_mission", "workspace_id", "mission_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="RESTRICT"),
        nullable=False)
    approval_id: Mapped[str | None] = mapped_column(ForeignKey("mission_approvals.id",
        ondelete="RESTRICT"), nullable=True)
    plan_id: Mapped[str | None] = mapped_column(
        ForeignKey("mission_plans.id", ondelete="RESTRICT"), nullable=True
    )
    plan_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_version: Mapped[int] = mapped_column(Integer, nullable=False)
    scenario_id: Mapped[str] = mapped_column(String(100), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="queued")
    lease_owner: Mapped[str | None] = mapped_column(String(128), nullable=True)
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),
        nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),
        nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    outcome: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_refs: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=_utcnow)


class MissionJobAttempt(Base):
    __tablename__ = "mission_job_attempts"
    __table_args__ = (
        UniqueConstraint("job_id", "attempt_number", name="uq_mission_job_attempt_number"),
        Index("ix_mission_job_attempt_status", "job_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_new_id)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="RESTRICT"),
        nullable=False)
    job_id: Mapped[str] = mapped_column(ForeignKey("mission_jobs.id", ondelete="RESTRICT"),
        nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    worker_id: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=_utcnow)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_category: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_refs: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    termination_confirmed: Mapped[bool] = mapped_column(default=False, nullable=False)
