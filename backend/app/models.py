"""Durable identity, world model, snapshot, mission, simulation and audit models."""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_id() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)


class WorkspaceMembership(Base):
    __tablename__ = "workspace_memberships"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id",
        ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="member")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)


class UserSession(Base):
    __tablename__ = "user_sessions"
    __table_args__ = (Index("ix_user_sessions_user_expiry", "user_id", "expires_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    csrf_token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)


class Mission(Base):
    __tablename__ = "missions"
    __table_args__ = (
        Index("ix_missions_workspace_created", "workspace_id", "created_at"),
        Index("ix_missions_requester", "requester_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id",
        ondelete="RESTRICT"), nullable=False)
    requester_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False)
    objective: Mapped[str] = mapped_column(String(500), nullable=False)
    scope: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    autonomy_tier: Mapped[str] = mapped_column(String(64), nullable=False,
        default="observe_explain")
    state: Mapped[str] = mapped_column(String(32), nullable=False, default="draft")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow, onupdate=utcnow)
    terminal_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completion_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)


class AuditEvent(Base):
    """Append-only through application services; no update/delete API is provided."""

    __tablename__ = "audit_events"
    __table_args__ = (Index("ix_audit_workspace_created", "workspace_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    workspace_id: Mapped[str | None] = mapped_column(ForeignKey("workspaces.id",
        ondelete="SET NULL"), nullable=True)
    actor_id: Mapped[str | None] = mapped_column(ForeignKey("users.id",
        ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    decision: Mapped[str] = mapped_column(String(32), nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    request_id: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)


class WorldEntity(Base):
    __tablename__ = "world_entities"
    __table_args__ = (Index("ix_world_entities_workspace_created", "workspace_id", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id",
        ondelete="RESTRICT"), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    environment_id: Mapped[str] = mapped_column(String(64), nullable=False, default="synthetic-lab")
    source_class: Mapped[str] = mapped_column(String(32), nullable=False, default="synthetic")
    attributes: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow, onupdate=utcnow)


class WorldRelationship(Base):
    __tablename__ = "world_relationships"
    __table_args__ = (Index("ix_world_relationships_workspace_created", "workspace_id",
        "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id",
        ondelete="RESTRICT"), nullable=False)
    from_entity_id: Mapped[str] = mapped_column(ForeignKey("world_entities.id",
        ondelete="RESTRICT"), nullable=False)
    to_entity_id: Mapped[str] = mapped_column(ForeignKey("world_entities.id",
        ondelete="RESTRICT"), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(40), nullable=False)
    source_class: Mapped[str] = mapped_column(String(32), nullable=False, default="synthetic")
    attributes: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False, default=dict)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)


class WorldSnapshot(Base):
    __tablename__ = "world_snapshots"
    __table_args__ = (
        UniqueConstraint("mission_id", "sequence", name="uq_world_snapshots_mission_sequence"),
        Index("ix_world_snapshots_workspace_mission", "workspace_id", "mission_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id",
        ondelete="RESTRICT"), nullable=False)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="RESTRICT"),
        nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    graph_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    captured_by: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    __table_args__ = (
        UniqueConstraint("workspace_id", "mission_id", "idempotency_key",
            name="uq_simrun_mission_idempotency"),
        Index("ix_simulation_runs_workspace_mission", "workspace_id", "mission_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id",
        ondelete="RESTRICT"), nullable=False)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="RESTRICT"),
        nullable=False)
    baseline_id: Mapped[str] = mapped_column(ForeignKey("world_snapshots.id",
        ondelete="RESTRICT"), nullable=False)
    scenario_id: Mapped[str] = mapped_column(String(100), nullable=False)
    fixture_version: Mapped[str] = mapped_column(String(32), nullable=False)
    rule_set_version: Mapped[str] = mapped_column(String(64), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    input_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    output_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    outcome: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    result: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"
    __table_args__ = (
        UniqueConstraint("run_id", "source_ref", "evidence_type",
            name="uq_evidence_run_source_type"),
        Index("ix_evidence_workspace_mission", "workspace_id", "mission_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id",
        ondelete="RESTRICT"), nullable=False)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="RESTRICT"),
        nullable=False)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id",
        ondelete="RESTRICT"), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    source_class: Mapped[str] = mapped_column(String(32), nullable=False, default="synthetic")
    source_ref: Mapped[str] = mapped_column(String(200), nullable=False)
    producer: Mapped[str] = mapped_column(String(100), nullable=False)
    producer_version: Mapped[str] = mapped_column(String(64), nullable=False)
    content_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    payload: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    limitations: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)


class OrigoVerification(Base):
    """Append-only record of one Origo verification attempt."""

    __tablename__ = "origo_verifications"
    __table_args__ = (
        CheckConstraint(
            "status IN ('verified', 'failed', 'disputed', 'inconclusive')",
            name="ck_origo_verification_status",
        ),
        UniqueConstraint("workspace_id", "run_id", "idempotency_key",
            name="uq_origo_verification_idempotency"),
        Index("ix_origo_verifications_workspace_mission_created",
            "workspace_id", "mission_id", "created_at"),
        Index("ix_origo_verifications_workspace_run_created",
            "workspace_id", "run_id", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    schema_version: Mapped[str] = mapped_column(String(16), nullable=False, default="1.0")
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id", ondelete="RESTRICT"),
        nullable=False)
    mission_id: Mapped[str] = mapped_column(ForeignKey("missions.id", ondelete="RESTRICT"),
        nullable=False)
    run_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="RESTRICT"),
        nullable=False)
    status: Mapped[str] = mapped_column(String(24), nullable=False)
    verifier_version: Mapped[str] = mapped_column(String(64), nullable=False)
    checks: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False, default=list)
    reasons: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    discrepancies: Mapped[list[dict[str, object]]] = mapped_column(
        JSON, nullable=False, default=list
    )
    evidence_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    evidence_fingerprints: Mapped[dict[str, str]] = mapped_column(
        JSON, nullable=False, default=dict
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False,
        default=utcnow)


# Register Stage 5 tables with shared SQLAlchemy metadata for Alembic.
import app.stage5_models  # noqa: E402, F401
