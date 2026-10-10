"""Persist append-only Origo verification history.

Revision ID: 0003_origo_verification
Revises: 0002_world_simulation
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_origo_verification"
down_revision: str | None = "0002_world_simulation"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "origo_verifications",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("workspace_id", sa.String(length=36),
                  sa.ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("mission_id", sa.String(length=36),
                  sa.ForeignKey("missions.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("run_id", sa.String(length=36),
                  sa.ForeignKey("simulation_runs.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("verifier_version", sa.String(length=64), nullable=False),
        sa.Column("checks", sa.JSON(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("discrepancies", sa.JSON(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("evidence_fingerprints", sa.JSON(), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "status IN ('verified', 'failed', 'disputed', 'inconclusive')",
            name="ck_origo_verification_status",
        ),
        sa.UniqueConstraint(
            "workspace_id", "run_id", "idempotency_key",
            name="uq_origo_verification_idempotency",
        ),
    )
    op.create_index(
        "ix_origo_verifications_workspace_mission_created",
        "origo_verifications", ["workspace_id", "mission_id", "created_at"],
    )
    op.create_index(
        "ix_origo_verifications_workspace_run_created",
        "origo_verifications", ["workspace_id", "run_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_origo_verifications_workspace_run_created", table_name="origo_verifications")
    op.drop_index("ix_origo_verifications_workspace_mission_created", table_name="origo_verifications")
    op.drop_table("origo_verifications")
