"""Workspace-authorized mission creation and retrieval."""

from fastapi import APIRouter, Depends, Header, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_csrf, require_workspace_membership
from app.errors import ApiError
from app.models import AuditEvent, Mission, User
from app.schemas import MissionCreate, MissionPublic, MissionScope

router = APIRouter(prefix="/missions", tags=["missions"])


def _mission_response(mission: Mission) -> MissionPublic:
    return MissionPublic(
        id=mission.id,
        schema_version=mission.schema_version,
        workspace_id=mission.workspace_id,
        requester_id=mission.requester_id,
        objective=mission.objective,
        scope=MissionScope.model_validate(mission.scope),
        autonomy_tier=mission.autonomy_tier,
        state=mission.state,
        version=mission.version,
        created_at=mission.created_at,
        updated_at=mission.updated_at,
    )


def _audit_mission(request: Request, user: User, mission: Mission) -> AuditEvent:
    return AuditEvent(
        actor_id=user.id,
        workspace_id=mission.workspace_id,
        action="mission.created",
        resource_type="mission",
        resource_id=mission.id,
        decision="allow",
        reason="synthetic_scope_draft_created",
        request_id=request.state.request_id,
    )


@router.post("", response_model=MissionPublic, status_code=201)
def create_mission(
    payload: MissionCreate,
    request: Request,
    user: User = Depends(get_current_user),
    _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> MissionPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    mission = Mission(
        workspace_id=workspace_id,
        requester_id=user.id,
        objective=payload.objective,
        scope=payload.scope.model_dump(mode="json"),
        autonomy_tier=payload.autonomy_tier,
        state="draft",
        schema_version="1.0",
        version=1,
    )
    db.add(mission)
    db.flush()
    db.add(_audit_mission(request, user, mission))
    db.commit()
    db.refresh(mission)
    return _mission_response(mission)


@router.get("", response_model=list[MissionPublic])
def list_missions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0, le=10000),
) -> list[MissionPublic]:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    rows = db.scalars(
        select(Mission)
        .where(Mission.workspace_id == workspace_id)
        .order_by(Mission.created_at.desc(), Mission.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return [_mission_response(mission) for mission in rows]


@router.get("/{mission_id}", response_model=MissionPublic)
def get_mission(
    mission_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> MissionPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    mission = db.scalar(
        select(Mission).where(Mission.id == mission_id, Mission.workspace_id == workspace_id)
    )
    if mission is None:
        raise ApiError(404, "MISSION_NOT_FOUND", "The requested mission was not found.")
    return _mission_response(mission)
