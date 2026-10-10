"""Stage 5 governance, lifecycle events and durable synthetic job records.

Revision ID: 0004_stage5_governance_jobs
Revises: 0003_origo_verification
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_stage5_governance_jobs"
down_revision: str | None = "0003_origo_verification"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("missions", sa.Column("terminal_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("missions", sa.Column("completion_reason", sa.String(length=200), nullable=True))
    op.create_table(
        "mission_transition_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("actor_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("actor_kind", sa.String(24), nullable=False),
        sa.Column("old_state", sa.String(32), nullable=False),
        sa.Column("new_state", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(200), nullable=False),
        sa.Column("request_id", sa.String(128), nullable=False),
        sa.Column("object_version", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_mission_transition_workspace_mission", "mission_transition_events", ["workspace_id", "mission_id", "created_at"])
    op.create_table(
        "mission_approvals",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("requester_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("approver_id", sa.String(36), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("action_class", sa.String(64), nullable=False),
        sa.Column("approved_scope", sa.JSON(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("plan_digest", sa.String(64), nullable=False),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column("decision", sa.String(24), nullable=False),
        sa.Column("decision_reason", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("invalidated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("decision IN ('approved', 'denied')", name="ck_mission_approval_decision"),
    )
    op.create_index("ix_mission_approval_workspace_mission", "mission_approvals", ["workspace_id", "mission_id", "created_at"])
    op.create_table(
        "mission_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("approval_id", sa.String(36), sa.ForeignKey("mission_approvals.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("plan_digest", sa.String(64), nullable=False),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column("scenario_id", sa.String(100), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("lease_owner", sa.String(128), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("outcome", sa.String(32), nullable=True),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("status IN ('queued','claimed','running','cancelling','succeeded','failed','cancelled','uncertain','review_required')", name="ck_mission_job_status"),
        sa.UniqueConstraint("workspace_id", "mission_id", "idempotency_key", name="uq_mission_job_idempotency"),
    )
    op.create_index("ix_mission_job_claim", "mission_jobs", ["status", "created_at"])
    op.create_index("ix_mission_job_workspace_mission", "mission_jobs", ["workspace_id", "mission_id"])
    op.create_table(
        "mission_job_attempts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("workspace_id", sa.String(36), sa.ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mission_id", sa.String(36), sa.ForeignKey("missions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("mission_jobs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("worker_id", sa.String(128), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_category", sa.String(64), nullable=True),
        sa.Column("evidence_refs", sa.JSON(), nullable=False),
        sa.Column("termination_confirmed", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("job_id", "attempt_number", name="uq_mission_job_attempt_number"),
    )
    op.create_index("ix_mission_job_attempt_status", "mission_job_attempts", ["job_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_mission_job_attempt_status", table_name="mission_job_attempts")
    op.drop_table("mission_job_attempts")
    op.drop_index("ix_mission_job_workspace_mission", table_name="mission_jobs")
    op.drop_index("ix_mission_job_claim", table_name="mission_jobs")
    op.drop_table("mission_jobs")
    op.drop_index("ix_mission_approval_workspace_mission", table_name="mission_approvals")
    op.drop_table("mission_approvals")
    op.drop_index("ix_mission_transition_workspace_mission", table_name="mission_transition_events")
    op.drop_table("mission_transition_events")
    op.drop_column("missions", "completion_reason")
    op.drop_column("missions", "terminal_at")
