"""Server-authoritative mission lifecycle transitions.

Only command names map to transitions. Clients never submit a target state.
Successful terminal outcomes require an explicitly trusted verifier caller.
"""
import hashlib
import json
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import AuditEvent, Mission, new_id
from app.stage5_models import MissionApproval, MissionTransitionEvent

CANONICAL_STATES = frozenset({
    "draft", "validating", "blocked_scope", "blocked_approval", "rejected", "ready",
    "planning", "planned", "queued", "running", "cancelling", "verifying", "succeeded",
    "completed_with_warnings", "disputed", "inconclusive", "failed", "cancelled", "expired",
})
TERMINAL_STATES = frozenset({
    "rejected", "succeeded", "completed_with_warnings", "disputed", "inconclusive",
    "failed", "cancelled", "expired",
})
ALLOWED_TRANSITIONS = {
    "draft": {"validating"},
    "validating": {"blocked_scope", "blocked_approval", "rejected", "ready"},
    "blocked_scope": {"validating"},
    "blocked_approval": {"validating"},
    "ready": {"planning"},
    "planning": {"planned", "failed"},
    "planned": {"blocked_approval", "queued"},
    "queued": {"running", "cancelled"},
    "running": {"cancelling", "verifying", "failed", "expired"},
    "cancelling": {"cancelled", "failed"},
    "verifying": {"succeeded", "completed_with_warnings", "disputed", "inconclusive", "failed"},
}
COMMAND_TARGETS = {
    "validate": "validating",
    "block_scope": "blocked_scope",
    "block_approval": "blocked_approval",
    "reject": "rejected",
    "validation_passed": "ready",
    "begin_planning": "planning",
    "plan_ready": "planned",
    "plan_failed": "failed",
    "require_approval": "blocked_approval",
    "queue": "queued",
    "start": "running",
    "cancel": "cancelling",
    "cancel_before_start": "cancelled",
    "begin_verification": "verifying",
    "fail": "failed",
    "expire": "expired",
    "cancelled": "cancelled",
    "verified_success": "succeeded",
    "verified_warnings": "completed_with_warnings",
    "verification_disputed": "disputed",
    "verification_inconclusive": "inconclusive",
    "verification_failed": "failed",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def canonical_mission_digest(mission: Mission) -> str:
    """Digest the persisted execution contract, not a model-generated plan."""
    canonical = json.dumps({
        "objective": mission.objective,
        "scope": mission.scope,
        "autonomy_tier": mission.autonomy_tier,
    }, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def transition_mission(
    db: Session, *, mission: Mission, actor_id: str | None, actor_kind: str,
    command: str, expected_version: int, reason: str, request_id: str,
    verifier_authorized: bool = False,
) -> Mission:
    """Apply one allowed transition using compare-and-swap and an audit record."""
    target = COMMAND_TARGETS.get(command)
    if target is None:
        raise ApiError(400, "UNKNOWN_MISSION_COMMAND", "The requested mission command is not supported.")
    if command.startswith("verified_") or command.startswith("verification_"):
        if not verifier_authorized:
            raise ApiError(403, "VERIFIER_AUTHORITY_REQUIRED", "Only the trusted verification path may set verification outcomes.")
    if mission.state not in CANONICAL_STATES:
        raise ApiError(409, "UNKNOWN_MISSION_STATE", "The stored mission state is not recognized; transition was blocked.")
    if mission.state in TERMINAL_STATES:
        raise ApiError(409, "MISSION_TERMINAL", "Terminal missions cannot be changed through normal workflow commands.")
    if target not in ALLOWED_TRANSITIONS.get(mission.state, set()):
        raise ApiError(409, "ILLEGAL_MISSION_TRANSITION", "The requested command is not allowed from the current mission state.")
    if expected_version != mission.version:
        raise ApiError(409, "MISSION_VERSION_CONFLICT", "The mission changed; reload its current state before retrying.")
    if not reason.strip() or len(reason.strip()) > 200:
        raise ApiError(422, "TRANSITION_REASON_REQUIRED", "Provide a concise transition reason.")
    if target == "queued":
        now = _now()
        approvals = db.scalars(select(MissionApproval).where(
            MissionApproval.workspace_id == mission.workspace_id,
            MissionApproval.mission_id == mission.id,
            MissionApproval.action_class == "synthetic_simulation",
            MissionApproval.decision == "approved",
            MissionApproval.plan_version == expected_version,
            MissionApproval.revoked_at.is_(None),
            MissionApproval.invalidated_at.is_(None),
            MissionApproval.consumed_at.is_(None),
            MissionApproval.expires_at > now,
        )).all()
        # OD-003/OD-015 remain open. Until policy/roles are owner-approved, fail closed.
        if not approvals:
            raise ApiError(409, "APPROVAL_REQUIRED", "No current, unconsumed approval is bound to this mission version and action.")
        if len(approvals) != 1:
            raise ApiError(409, "APPROVAL_AMBIGUOUS", "Approval records are contradictory; queueing is blocked.")
        approval = approvals[0]
        if (
            approval.requester_id != mission.requester_id
            or approval.approver_id is None
            or approval.approver_id == mission.requester_id
            or approval.approved_scope != mission.scope
            or approval.plan_digest != canonical_mission_digest(mission)
        ):
            raise ApiError(409, "APPROVAL_BINDING_MISMATCH", "Approval requester or scope does not match the mission.")
        approval.consumed_at = now
    now = _now()
    terminal_at = now if target in TERMINAL_STATES else None
    result = db.execute(update(Mission).where(
        Mission.id == mission.id,
        Mission.workspace_id == mission.workspace_id,
        Mission.version == expected_version,
        Mission.state == mission.state,
    ).values(
        state=target,
        version=Mission.version + 1,
        updated_at=now,
        terminal_at=terminal_at,
        completion_reason=reason.strip() if target in TERMINAL_STATES else None,
    ))
    if result.rowcount != 1:
        db.rollback()
        raise ApiError(409, "MISSION_VERSION_CONFLICT", "A concurrent transition won; reload the mission.")
    new_version = expected_version + 1
    db.add(MissionTransitionEvent(
        id=new_id(), workspace_id=mission.workspace_id, mission_id=mission.id,
        actor_id=actor_id, actor_kind=actor_kind, old_state=mission.state,
        new_state=target, reason=reason.strip(), request_id=request_id,
        object_version=new_version, metadata_json={},
    ))
    db.add(AuditEvent(
        actor_id=actor_id, workspace_id=mission.workspace_id,
        action="mission.state_transition", resource_type="mission",
        resource_id=mission.id, decision="allow",
        reason=f"{mission.state}_to_{target}:{reason.strip()[:120]}",
        request_id=request_id,
    ))
    db.flush()
    db.refresh(mission)
    return mission
