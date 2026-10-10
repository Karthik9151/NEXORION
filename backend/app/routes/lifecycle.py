"""Authenticated commands for the server-owned mission lifecycle."""
from fastapi import APIRouter, Depends, Header, Request
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_csrf, require_workspace_membership
from app.errors import ApiError
from app.models import Mission, User
from app.schemas import MissionPublic, StrictModel, MissionScope
from app.services.lifecycle import transition_mission

router = APIRouter(prefix="/missions", tags=["mission-lifecycle"])


class MissionCommand(StrictModel):
    command: str = Field(min_length=1, max_length=40)
    expected_version: int = Field(ge=1)
    reason: str = Field(min_length=1, max_length=200)


def _public(mission: Mission) -> MissionPublic:
    return MissionPublic(
        id=mission.id, schema_version=mission.schema_version, workspace_id=mission.workspace_id,
        requester_id=mission.requester_id, objective=mission.objective,
        scope=MissionScope.model_validate(mission.scope), autonomy_tier=mission.autonomy_tier,
        state=mission.state, version=mission.version, created_at=mission.created_at,
        updated_at=mission.updated_at,
    )


@router.post("/{mission_id}/commands", response_model=MissionPublic)
def mission_command(
    mission_id: str, payload: MissionCommand, request: Request,
    user: User = Depends(get_current_user), _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> MissionPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    if payload.command == "queue":
        raise ApiError(400, "USE_DURABLE_JOB_QUEUE", "Queueing must use the durable job endpoint so idempotency and approval are enforced.")
    mission = db.scalar(select(Mission).where(
        Mission.id == mission_id, Mission.workspace_id == workspace_id,
    ))
    if mission is None:
        raise ApiError(404, "MISSION_NOT_FOUND", "The requested mission was not found.")
    try:
        transition_mission(
            db, mission=mission, actor_id=user.id, actor_kind="user",
            command=payload.command, expected_version=payload.expected_version,
            reason=payload.reason, request_id=request.state.request_id,
            verifier_authorized=False,
        )
        db.commit()
        db.refresh(mission)
    except Exception:
        db.rollback()
        raise
    return _public(mission)
