"""PostgreSQL-only Stage 5 compare-and-swap concurrency test."""
import os
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import Mission, User, Workspace, WorkspaceMembership
from app.services.lifecycle import transition_mission

DATABASE_URL = os.environ.get("NEXORION_TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not DATABASE_URL, reason="PostgreSQL 16 integration URL not configured")


def test_concurrent_lifecycle_commands_have_one_winner() -> None:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    suffix = uuid4().hex
    with Session(engine) as db:
        user = User(email=f"stage5-{suffix}@example.test", password_hash="test-only-not-a-credential")
        workspace = Workspace(name=f"stage5-{suffix}")
        db.add_all([user, workspace])
        db.flush()
        db.add(WorkspaceMembership(user_id=user.id, workspace_id=workspace.id, role="owner"))
        mission = Mission(
            workspace_id=workspace.id, requester_id=user.id,
            objective="Verify PostgreSQL lifecycle compare-and-swap behavior",
            scope={"mode": "synthetic_only", "scenario_ids": ["scenario-auth-failure-v1"],
                   "entity_ids": [], "excluded_targets": ["external systems", "real credentials"]},
            autonomy_tier="observe_explain", state="draft", version=1,
        )
        db.add(mission)
        db.commit()
        mission_id, workspace_id, actor_id = mission.id, workspace.id, user.id

    barrier = Barrier(2)

    def contender() -> str:
        with Session(engine) as db:
            mission = db.scalar(select(Mission).where(Mission.id == mission_id))
            assert mission is not None
            barrier.wait(timeout=10)
            try:
                transition_mission(
                    db, mission=mission, actor_id=actor_id, actor_kind="postgres-test",
                    command="validate", expected_version=1, reason="concurrency test",
                    request_id=f"stage5-{suffix}",
                )
                db.commit()
                return "committed"
            except ApiError as exc:
                db.rollback()
                assert exc.code == "MISSION_VERSION_CONFLICT"
                return "conflict"

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: contender(), range(2)))
        assert sorted(results) == ["committed", "conflict"]
        with Session(engine) as db:
            final = db.scalar(select(Mission).where(
                Mission.id == mission_id, Mission.workspace_id == workspace_id,
            ))
            assert final is not None
            assert final.state == "validating"
            assert final.version == 2
    finally:
        engine.dispose()
