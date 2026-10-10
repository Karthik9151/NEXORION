"""Add the synthetic digital-world graph, baselines, runs and evidence.

Revision ID: 0002_world_simulation
Revises: 0001_initial
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_world_simulation"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "world_entities",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("entity_type", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("environment_id", sa.String(length=64), nullable=False),
        sa.Column("source_class", sa.String(length=32), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_world_entities_workspace_created", "world_entities",
        ["workspace_id", "created_at"])

    op.create_table(
        "world_relationships",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("from_entity_id", sa.String(length=36),
            sa.ForeignKey("world_entities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("to_entity_id", sa.String(length=36), sa.ForeignKey("world_entities.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("relationship_type", sa.String(length=40), nullable=False),
        sa.Column("source_class", sa.String(length=32), nullable=False),
        sa.Column("attributes", sa.JSON(), nullable=False),
        sa.Column("created_by", sa.String(length=36), sa.ForeignKey("users.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_world_relationships_workspace_created", "world_relationships",
        ["workspace_id", "created_at"])

    op.create_table(
        "world_snapshots",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("mission_id", sa.String(length=36), sa.ForeignKey("missions.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("graph_digest", sa.String(length=64), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("captured_by", sa.String(length=36), sa.ForeignKey("users.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("mission_id", "sequence", name="uq_world_snapshots_mission_sequence"),
    )
    op.create_index("ix_world_snapshots_workspace_mission", "world_snapshots",
        ["workspace_id", "mission_id"])

    op.create_table(
        "simulation_runs",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("mission_id", sa.String(length=36), sa.ForeignKey("missions.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("baseline_id", sa.String(length=36), sa.ForeignKey("world_snapshots.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("scenario_id", sa.String(length=100), nullable=False),
        sa.Column("fixture_version", sa.String(length=32), nullable=False),
        sa.Column("rule_set_version", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("input_digest", sa.String(length=64), nullable=False),
        sa.Column("output_digest", sa.String(length=64), nullable=False),
        sa.Column("outcome", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("workspace_id", "mission_id", "idempotency_key",
            name="uq_simrun_mission_idempotency"),
    )
    op.create_index("ix_simulation_runs_workspace_mission", "simulation_runs",
        ["workspace_id", "mission_id"])

    op.create_table(
        "evidence_records",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("schema_version", sa.String(length=16), nullable=False),
        sa.Column("workspace_id", sa.String(length=36), sa.ForeignKey("workspaces.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("mission_id", sa.String(length=36), sa.ForeignKey("missions.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("run_id", sa.String(length=36), sa.ForeignKey("simulation_runs.id",
            ondelete="RESTRICT"), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("source_class", sa.String(length=32), nullable=False),
        sa.Column("source_ref", sa.String(length=200), nullable=False),
        sa.Column("producer", sa.String(length=100), nullable=False),
        sa.Column("producer_version", sa.String(length=64), nullable=False),
        sa.Column("content_digest", sa.String(length=64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("limitations", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("run_id", "source_ref", "evidence_type",
            name="uq_evidence_run_source_type"),
    )
    op.create_index("ix_evidence_workspace_mission", "evidence_records", ["workspace_id",
        "mission_id"])


def downgrade() -> None:
    op.drop_index("ix_evidence_workspace_mission", table_name="evidence_records")
    op.drop_table("evidence_records")
    op.drop_index("ix_simulation_runs_workspace_mission", table_name="simulation_runs")
    op.drop_table("simulation_runs")
    op.drop_index("ix_world_snapshots_workspace_mission", table_name="world_snapshots")
    op.drop_table("world_snapshots")
    op.drop_index("ix_world_relationships_workspace_created", table_name="world_relationships")
    op.drop_table("world_relationships")
    op.drop_index("ix_world_entities_workspace_created", table_name="world_entities")
    op.drop_table("world_entities")
