"""Scoped mission approval commands.

Provisional safe default (not a finalized organizational policy): a distinct
workspace owner must approve each synthetic execution; no self-approval.
OD-003 and OD-015 remain explicitly open for owner review.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, Request
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_csrf, require_workspace_membership
from app.errors import ApiError
from app.models import AuditEvent, Mission, User, WorkspaceMembership
from app.schemas import StrictModel
from app.services.lifecycle import canonical_mission_digest
from app.stage5_models import MissionApproval

router = APIRouter(prefix="/missions", tags=["mission-approvals"])


class ApprovalDecisionRequest(StrictModel):
    decision: str = Field(pattern="^(approved|denied)$")
    reason: str = Field(min_length=1, max_length=200)
    expires_in_minutes: int = Field(default=15, ge=5, le=60)


class ApprovalPublic(StrictModel):
    id: str
    workspace_id: str
    mission_id: str
    requester_id: str
    approver_id: str | None
    action_class: str
    approved_scope: dict[str, object]
    constraints: dict[str, object]
    plan_digest: str
    plan_version: int
    decision: str
    decision_reason: str
    created_at: datetime
    expires_at: datetime
    consumed_at: datetime | None
    revoked_at: datetime | None
    invalidated_at: datetime | None


def _require_owner(db: Session, user: User, workspace_id: str) -> None:
    membership = db.scalar(select(WorkspaceMembership).where(
        WorkspaceMembership.user_id == user.id,
        WorkspaceMembership.workspace_id == workspace_id,
    ))
    if membership is None or membership.role != "owner":
        raise ApiError(403, "APPROVER_ROLE_REQUIRED", "Only a workspace owner may issue or revoke approvals under the provisional Stage 5 policy.")


def _public(item: MissionApproval) -> ApprovalPublic:
    return ApprovalPublic(
        id=item.id, workspace_id=item.workspace_id, mission_id=item.mission_id,
        requester_id=item.requester_id, approver_id=item.approver_id,
        action_class=item.action_class, approved_scope=item.approved_scope,
        constraints=item.constraints, plan_digest=item.plan_digest,
        plan_version=item.plan_version, decision=item.decision,
        decision_reason=item.decision_reason, created_at=item.created_at,
        expires_at=item.expires_at, consumed_at=item.consumed_at,
        revoked_at=item.revoked_at, invalidated_at=item.invalidated_at,
    )


@router.post("/{mission_id}/approvals", response_model=ApprovalPublic, status_code=201)
def decide_approval(
    mission_id: str, payload: ApprovalDecisionRequest, request: Request,
    user: User = Depends(get_current_user), _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> ApprovalPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    _require_owner(db, user, workspace_id)
    mission = db.scalar(select(Mission).where(
        Mission.id == mission_id, Mission.workspace_id == workspace_id,
    ))
    if mission is None:
        raise ApiError(404, "MISSION_NOT_FOUND", "The requested mission was not found.")
    if mission.state != "planned":
        raise ApiError(409, "MISSION_NOT_PLANNED", "Approval can be issued only for a planned mission.")
    if user.id == mission.requester_id:
        raise ApiError(403, "SEPARATION_OF_DUTIES_REQUIRED", "The mission requester cannot approve their own execution.")
    now = datetime.now(timezone.utc)
    record = MissionApproval(
        workspace_id=mission.workspace_id, mission_id=mission.id,
        requester_id=mission.requester_id, approver_id=user.id,
        action_class="synthetic_simulation", approved_scope=mission.scope,
        constraints={"synthetic_only": True, "registered_scenarios_only": True},
        plan_digest=canonical_mission_digest(mission), plan_version=mission.version,
        decision=payload.decision, decision_reason=payload.reason.strip(),
        created_at=now, expires_at=now + timedelta(minutes=payload.expires_in_minutes),
    )
    db.add(record)
    db.flush()
    db.add(AuditEvent(
        actor_id=user.id, workspace_id=workspace_id, action="mission.approval_decision",
        resource_type="mission_approval", resource_id=record.id, decision=payload.decision,
        reason=payload.reason.strip(), request_id=request.state.request_id,
    ))
    db.commit()
    db.refresh(record)
    return _public(record)


@router.post("/{mission_id}/approvals/{approval_id}/revoke", response_model=ApprovalPublic)
def revoke_approval(
    mission_id: str, approval_id: str, request: Request,
    user: User = Depends(get_current_user), _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    workspace_id: str | None = Header(default=None, alias="X-Workspace-ID"),
) -> ApprovalPublic:
    require_workspace_membership(db, user_id=user.id, workspace_id=workspace_id)
    _require_owner(db, user, workspace_id)
    record = db.scalar(select(MissionApproval).where(
        MissionApproval.id == approval_id,
        MissionApproval.mission_id == mission_id,
        MissionApproval.workspace_id == workspace_id,
    ))
    if record is None:
        raise ApiError(404, "APPROVAL_NOT_FOUND", "The requested approval was not found.")
    if record.consumed_at is not None:
        raise ApiError(409, "APPROVAL_ALREADY_CONSUMED", "A consumed approval cannot be revoked retroactively.")
    if record.revoked_at is None:
        record.revoked_at = datetime.now(timezone.utc)
        db.add(AuditEvent(
            actor_id=user.id, workspace_id=workspace_id, action="mission.approval_revoked",
            resource_type="mission_approval", resource_id=record.id, decision="allow",
            reason="workspace_owner_revoked_approval", request_id=request.state.request_id,
        ))
        db.commit()
        db.refresh(record)
    return _public(record)
