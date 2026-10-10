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
    # Keep the wider column: narrowing could fail or lose meaning when a
    # persisted outcome exceeds 32 characters. A 64-character column remains
    # compatible with the prior schema and is safe to leave widened on rollback.
    pass
