"""Persist immutable typed mission plans and bind approvals/jobs to them.

Revision ID: 0006_immutable_mission_plans
Revises: 0005_widen_mission_job_outcome
"""
from collections.abc import Sequence
from datetime import datetime, timezone
import hashlib
import json
from uuid import uuid4

import sqlalchemy as sa
from alembic import op

revision: str = "0006_immutable_mission_plans"
down_revision: str | None = "0005_widen_mission_job_outcome"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _canonical_document(objective: str, scope: object, autonomy_tier: str) -> dict[str, object]:
    return {
        "objective": objective,
        "scope": scope,
        "autonomy_tier": autonomy_tier,
    }


def _digest(document: dict[str, object]) -> str:
    canonical = json.dumps(
        document,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _install_immutability_triggers(bind: sa.Connection) -> None:
    if bind.dialect.name == "sqlite":
        op.execute(
            """
            CREATE TRIGGER trg_mission_plans_no_update
            BEFORE UPDATE ON mission_plans
            BEGIN
                SELECT RAISE(ABORT, 'mission plans are immutable');
            END
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_mission_plans_no_delete
            BEFORE DELETE ON mission_plans
            BEGIN
                SELECT RAISE(ABORT, 'mission plans are immutable');
            END
            """
        )
    elif bind.dialect.name == "postgresql":
        op.execute(
            """
            CREATE FUNCTION nexorion_reject_mission_plan_mutation()
            RETURNS trigger
            LANGUAGE plpgsql
            AS $function$
            BEGIN
                RAISE EXCEPTION 'mission plans are immutable';
            END;
            $function$;
            """
        )
        op.execute(
            """
            CREATE TRIGGER trg_mission_plans_immutable
            BEFORE UPDATE OR DELETE ON mission_plans
            FOR EACH ROW
            EXECUTE FUNCTION nexorion_reject_mission_plan_mutation();
            """
        )


def _backfill_existing_references(bind: sa.Connection) -> None:
    """Link old matching approvals/jobs; leave mismatched contracts fail-closed."""
    missions = sa.table(
        "missions",
        sa.column("id", sa.String(36)),
        sa.column("workspace_id", sa.String(36)),
        sa.column("requester_id", sa.String(36)),
        sa.column("objective", sa.String(500)),
        sa.column("scope", sa.JSON()),
        sa.column("autonomy_tier", sa.String(64)),
    )
    plan_table = sa.table(
        "mission_plans",
        sa.column("id", sa.String(36)),
        sa.column("workspace_id", sa.String(36)),
        sa.column("mission_id", sa.String(36)),
        sa.column("plan_version", sa.Integer()),
        sa.column("schema_version", sa.String(16)),
        sa.column("plan_digest", sa.String(64)),
        sa.column("plan_document", sa.JSON()),
        sa.column("created_by", sa.String(36)),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    sources = [
        sa.table(
            "mission_approvals",
            sa.column("workspace_id", sa.String(36)),
            sa.column("mission_id", sa.String(36)),
            sa.column("plan_version", sa.Integer()),
            sa.column("plan_digest", sa.String(64)),
            sa.column("plan_id", sa.String(36)),
        ),
        sa.table(
            "mission_jobs",
            sa.column("workspace_id", sa.String(36)),
            sa.column("mission_id", sa.String(36)),
            sa.column("plan_version", sa.Integer()),
            sa.column("plan_digest", sa.String(64)),
            sa.column("plan_id", sa.String(36)),
        ),
    ]
    now = datetime.now(timezone.utc)
    plans: dict[tuple[str, str, int], dict[str, object]] = {}

    for source in sources:
        rows = bind.execute(
            sa.select(
                source.c.workspace_id.label("workspace_id"),
                source.c.mission_id.label("mission_id"),
                source.c.plan_version.label("plan_version"),
                source.c.plan_digest.label("stored_digest"),
                missions.c.requester_id.label("requester_id"),
                missions.c.objective.label("objective"),
                missions.c.scope.label("scope"),
                missions.c.autonomy_tier.label("autonomy_tier"),
            ).select_from(
                source.join(
                    missions,
                    sa.and_(
                        missions.c.id == source.c.mission_id,
                        missions.c.workspace_id == source.c.workspace_id,
                    ),
                )
            )
        ).mappings()

        for row in rows:
            key = (
                row["workspace_id"],
                row["mission_id"],
                row["plan_version"],
            )
            document = _canonical_document(
                row["objective"], row["scope"], row["autonomy_tier"]
            )
            actual_digest = _digest(document)
            # Do not bless stale or contradictory approval/job records during
            # migration. Unmatched legacy rows remain NULL and will fail closed.
            if actual_digest != row["stored_digest"]:
                continue
            existing = plans.get(key)
            if existing is not None:
                if (
                    existing["plan_digest"] != actual_digest
                    or existing["plan_document"] != document
                ):
                    plans.pop(key)
                continue
            plans[key] = {
                "id": str(uuid4()),
                "workspace_id": key[0],
                "mission_id": key[1],
                "plan_version": key[2],
                "schema_version": "1.0",
                "plan_digest": actual_digest,
                "plan_document": document,
                "created_by": row["requester_id"],
                "created_at": now,
            }

    if plans:
        bind.execute(sa.insert(plan_table), list(plans.values()))

    for source in sources:
        for key, plan in plans.items():
            bind.execute(
                source.update().where(
                    source.c.workspace_id == key[0],
                    source.c.mission_id == key[1],
                    source.c.plan_version == key[2],
                    source.c.plan_digest == plan["plan_digest"],
                ).values(plan_id=plan["id"])
            )


def upgrade() -> None:
    op.create_table(
        "mission_plans",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "workspace_id",
            sa.String(36),
            sa.ForeignKey("workspaces.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "mission_id",
            sa.String(36),
            sa.ForeignKey("missions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("plan_version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(16), nullable=False),
        sa.Column("plan_digest", sa.String(64), nullable=False),
        sa.Column("plan_document", sa.JSON(), nullable=False),
        sa.Column(
            "created_by",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "workspace_id", "mission_id", "plan_version",
            name="uq_mission_plan_version",
        ),
    )
    op.create_index(
        "ix_mission_plan_workspace_mission",
        "mission_plans",
        ["workspace_id", "mission_id"],
    )
    op.add_column(
        "mission_approvals",
        sa.Column(
            "plan_id",
            sa.String(36),
            sa.ForeignKey("mission_plans.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.add_column(
        "mission_jobs",
        sa.Column(
            "plan_id",
            sa.String(36),
            sa.ForeignKey("mission_plans.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )
    op.create_index("ix_mission_approvals_plan", "mission_approvals", ["plan_id"])
    op.create_index("ix_mission_jobs_plan", "mission_jobs", ["plan_id"])

    bind = op.get_bind()
    _backfill_existing_references(bind)
    _install_immutability_triggers(bind)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS trg_mission_plans_no_update")
        op.execute("DROP TRIGGER IF EXISTS trg_mission_plans_no_delete")
    elif bind.dialect.name == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS trg_mission_plans_immutable ON mission_plans")
        op.execute("DROP FUNCTION IF EXISTS nexorion_reject_mission_plan_mutation()")

    op.drop_index("ix_mission_jobs_plan", table_name="mission_jobs")
    op.drop_index("ix_mission_approvals_plan", table_name="mission_approvals")
    with op.batch_alter_table("mission_jobs") as batch_op:
        batch_op.drop_column("plan_id")
    with op.batch_alter_table("mission_approvals") as batch_op:
        batch_op.drop_column("plan_id")
    op.drop_index("ix_mission_plan_workspace_mission", table_name="mission_plans")
    op.drop_table("mission_plans")
