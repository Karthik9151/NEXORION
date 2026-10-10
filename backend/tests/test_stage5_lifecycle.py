"""Stage 5 lifecycle contract tests; use isolated SQLite only for state-machine semantics."""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.errors import ApiError
from app.models import Mission, User, Workspace, WorkspaceMembership
from app.services.lifecycle import (
    ALLOWED_TRANSITIONS,
    CANONICAL_STATES,
    COMMAND_TARGETS,
    TERMINAL_STATES,
    canonical_mission_digest,
    transition_mission,
)
from app.stage5_models import MissionApproval

COMMAND_FOR_TARGET = {
    target: command for command, target in COMMAND_TARGETS.items()
}


def _database():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine


def _mission(db: Session, state: str) -> Mission:
    user = User(email="stage5@example.test", password_hash="not-a-real-secret")
    workspace = Workspace(name="Stage 5 test workspace")
    db.add_all([user, workspace])
    db.flush()
    db.add(WorkspaceMembership(user_id=user.id, workspace_id=workspace.id, role="owner"))
    mission = Mission(
        workspace_id=workspace.id,
        requester_id=user.id,
        objective="Review a bounded synthetic authentication scenario",
        scope={
            "mode": "synthetic_only",
            "scenario_ids": ["scenario-auth-failure-v1"],
            "entity_ids": [],
            "excluded_targets": ["all external systems", "all real credentials"],
        },
        autonomy_tier="simulate_synthetic",
        state=state,
        version=1,
    )
    db.add(mission)
    db.flush()
    return mission


def _command_for_target(target: str) -> tuple[str, bool]:
    if target in {"succeeded", "completed_with_warnings", "disputed", "inconclusive"}:
        return COMMAND_FOR_TARGET[target], True
    if target == "failed" and any(
        command in {"plan_failed", "fail", "verification_failed"}
        for command, mapped in COMMAND_TARGETS.items() if mapped == target
    ):
        # The source state determines whether this is a verifier-only transition below.
        return "fail", False
    return COMMAND_FOR_TARGET[target], False


@pytest.mark.parametrize(
    ("source", "target"),
    [(source, target) for source, targets in ALLOWED_TRANSITIONS.items() for target in targets],
)
def test_every_documented_transition_is_enforced(source: str, target: str) -> None:
    engine = _database()
    try:
        with Session(engine, expire_on_commit=False) as db:
            mission = _mission(db, source)
            verifier = target in {"succeeded", "completed_with_warnings", "disputed", "inconclusive"}
            if source == "verifying" and target == "failed":
                command, verifier = "verification_failed", True
            elif target == "failed" and source == "planning":
                command = "plan_failed"
            elif target == "failed":
                command = "fail"
            else:
                command = COMMAND_FOR_TARGET[target]
            if target == "queued":
                db.add(MissionApproval(
                    workspace_id=mission.workspace_id,
                    mission_id=mission.id,
                    requester_id=mission.requester_id,
                    approver_id="different-approver-id",
                    action_class="synthetic_simulation",
                    approved_scope=mission.scope,
                    constraints={},
                    plan_digest=canonical_mission_digest(mission),
                    plan_version=mission.version,
                    decision="approved",
                    decision_reason="isolated lifecycle test",
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                ))
                db.flush()
            transition_mission(
                db, mission=mission, actor_id=mission.requester_id,
                actor_kind="test", command=command, expected_version=1,
                reason="transition matrix test", request_id="stage5-test-001",
                verifier_authorized=verifier,
            )
            assert mission.state == target
            assert mission.version == 2
            if target in TERMINAL_STATES:
                assert mission.terminal_at is not None
                assert mission.completion_reason == "transition matrix test"
    finally:
        engine.dispose()


def test_all_canonical_states_are_present() -> None:
    assert len(CANONICAL_STATES) == 19
    assert {"draft", "validating", "blocked_scope", "blocked_approval", "rejected", "ready",
            "planning", "planned", "queued", "running", "cancelling", "verifying", "succeeded",
            "completed_with_warnings", "disputed", "inconclusive", "failed", "cancelled",
            "expired"} == CANONICAL_STATES


def test_client_cannot_submit_arbitrary_state() -> None:
    engine = _database()
    try:
        with Session(engine) as db:
            mission = _mission(db, "draft")
            with pytest.raises(ApiError) as error:
                transition_mission(
                    db, mission=mission, actor_id=mission.requester_id, actor_kind="user",
                    command="set_state", expected_version=1, reason="forged state",
                    request_id="stage5-test-002",
                )
            assert error.value.code == "UNKNOWN_MISSION_COMMAND"
    finally:
        engine.dispose()


@pytest.mark.parametrize("terminal", sorted(TERMINAL_STATES))
def test_terminal_states_cannot_be_mutated(terminal: str) -> None:
    engine = _database()
    try:
        with Session(engine) as db:
            mission = _mission(db, terminal)
            with pytest.raises(ApiError) as error:
                transition_mission(
                    db, mission=mission, actor_id=mission.requester_id, actor_kind="user",
                    command="validate", expected_version=1, reason="attempt reopen",
                    request_id="stage5-test-003",
                )
            assert error.value.code == "MISSION_TERMINAL"
    finally:
        engine.dispose()


def test_success_outcome_requires_verifier_authority() -> None:
    engine = _database()
    try:
        with Session(engine) as db:
            mission = _mission(db, "verifying")
            with pytest.raises(ApiError) as error:
                transition_mission(
                    db, mission=mission, actor_id=mission.requester_id, actor_kind="user",
                    command="verified_success", expected_version=1, reason="forged success",
                    request_id="stage5-test-004", verifier_authorized=False,
                )
            assert error.value.code == "VERIFIER_AUTHORITY_REQUIRED"
    finally:
        engine.dispose()


def test_stale_version_is_rejected() -> None:
    engine = _database()
    try:
        with Session(engine) as db:
            mission = _mission(db, "draft")
            with pytest.raises(ApiError) as error:
                transition_mission(
                    db, mission=mission, actor_id=mission.requester_id, actor_kind="user",
                    command="validate", expected_version=0, reason="stale update",
                    request_id="stage5-test-005",
                )
            assert error.value.code == "MISSION_VERSION_CONFLICT"
    finally:
        engine.dispose()


def test_queue_rejects_changed_plan_digest() -> None:
    engine = _database()
    try:
        with Session(engine) as db:
            mission = _mission(db, "planned")
            db.add(MissionApproval(
                workspace_id=mission.workspace_id, mission_id=mission.id,
                requester_id=mission.requester_id, approver_id="different-approver-id",
                action_class="synthetic_simulation", approved_scope=mission.scope,
                constraints={}, plan_digest="0" * 64, plan_version=mission.version,
                decision="approved", decision_reason="stale plan",
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
            ))
            db.flush()
            with pytest.raises(ApiError) as error:
                transition_mission(
                    db, mission=mission, actor_id=mission.requester_id, actor_kind="user",
                    command="queue", expected_version=1, reason="stale plan digest",
                    request_id="stage5-test-006",
                )
            assert error.value.code == "APPROVAL_BINDING_MISMATCH"
    finally:
        engine.dispose()
