"""Widen mission job outcome values without rewriting applied migration history.

Revision ID: 0005_widen_mission_job_outcome
Revises: 0004_stage5_governance_jobs
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_widen_mission_job_outcome"
down_revision: str | None = "0004_stage5_governance_jobs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("mission_jobs") as batch_op:
        batch_op.alter_column(
            "outcome",
            existing_type=sa.String(length=32),
            type_=sa.String(length=64),
            existing_nullable=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("mission_jobs") as batch_op:
        batch_op.alter_column(
            "outcome",
            existing_type=sa.String(length=64),
            type_=sa.String(length=32),
            existing_nullable=True,
        )
