"""Registration, login, session, and workspace listing endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, require_csrf
from app.errors import ApiError
from app.models import AuditEvent, User, UserSession, Workspace, WorkspaceMembership
from app.schemas import AuthResponse, LoginRequest, RegisterRequest, UserPublic, WorkspacePublic
from app.security import (
    hash_password,
    hash_session_token,
    is_expired,
    issue_session,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


def _workspace_results(db: Session, user_id: str) -> list[WorkspacePublic]:
    rows = db.execute(
        select(Workspace, WorkspaceMembership)
        .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
        .where(WorkspaceMembership.user_id == user_id)
        .order_by(Workspace.created_at.asc(), Workspace.id.asc())
    ).all()
    return [
        WorkspacePublic(
            id=workspace.id,
            name=workspace.name,
            role=membership.role,
            created_at=workspace.created_at,
        )
        for workspace, membership in rows
    ]


def _auth_response(user: User, db: Session) -> AuthResponse:
    return AuthResponse(
        user=UserPublic(id=user.id, email=user.email, created_at=user.created_at),
        workspaces=_workspace_results(db, user.id),
    )


def _set_session_cookies(
    response: Response, request: Request, raw_token: str, csrf_token: str
) -> None:
    settings = request.app.state.settings
    max_age = settings.session_ttl_hours * 60 * 60
    response.set_cookie(
        key=settings.session_cookie_name,
        value=raw_token,
        max_age=max_age,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        max_age=max_age,
        httponly=False,
        secure=settings.session_cookie_secure,
        samesite="strict",
        path="/",
    )


def _audit(
    *,
    action: str,
    resource_type: str,
    resource_id: str | None,
    request_id: str,
    actor_id: str | None = None,
    workspace_id: str | None = None,
    reason: str = "request_accepted",
) -> AuditEvent:
    return AuditEvent(
        actor_id=actor_id,
        workspace_id=workspace_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        decision="allow",
        reason=reason,
        request_id=request_id,
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    settings = request.app.state.settings
    if not settings.allow_self_registration:
        raise ApiError(403, "REGISTRATION_DISABLED", "Self-registration is disabled.")

    email = payload.email.lower().strip()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise ApiError(409, "ACCOUNT_ALREADY_EXISTS", "An account with that email already exists.")

    user = User(email=email, password_hash=hash_password(payload.password))
    workspace = Workspace(name=payload.workspace_name or f"{email.split('@', 1)[0]}'s Workspace")
    try:
        db.add_all([user, workspace])
        db.flush()
        db.add(WorkspaceMembership(user_id=user.id, workspace_id=workspace.id, role="owner"))
        db.add(
            _audit(
                action="user.registered",
                resource_type="user",
                resource_id=user.id,
                request_id=request.state.request_id,
                actor_id=user.id,
                workspace_id=workspace.id,
            )
        )
        db.add(
            _audit(
                action="workspace.created",
                resource_type="workspace",
                resource_id=workspace.id,
                request_id=request.state.request_id,
                actor_id=user.id,
                workspace_id=workspace.id,
            )
        )
        raw_token, csrf_token, session_record = issue_session(user.id, settings)
        db.add(session_record)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ApiError(
            409,
            "ACCOUNT_ALREADY_EXISTS",
            "An account with that email already exists.",
        ) from exc
    db.refresh(user)
    _set_session_cookies(response, request, raw_token, csrf_token)
    return _auth_response(user, db)


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> AuthResponse:
    email = payload.email.lower().strip()
    user = db.scalar(select(User).where(User.email == email))
    password_ok = verify_password(payload.password, user.password_hash if user else None)
    if user is None or not user.is_active or not password_ok:
        raise ApiError(401, "INVALID_CREDENTIALS", "Email or password is incorrect.")

    raw_token, csrf_token, session_record = issue_session(user.id, request.app.state.settings)
    db.add(session_record)
    db.add(
        _audit(
            action="user.login",
            resource_type="user",
            resource_id=user.id,
            request_id=request.state.request_id,
            actor_id=user.id,
            reason="session_created",
        )
    )
    db.commit()
    _set_session_cookies(response, request, raw_token, csrf_token)
    return _auth_response(user, db)


@router.get("/me", response_model=AuthResponse)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AuthResponse:
    return _auth_response(user, db)


@router.post("/logout", status_code=204)
def logout(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user),
    _csrf_ok: None = Depends(require_csrf),
    db: Session = Depends(get_db),
) -> Response:
    settings = request.app.state.settings
    token = request.cookies.get(settings.session_cookie_name, "")
    session_record = db.scalar(
        select(UserSession).where(UserSession.token_hash == hash_session_token(token))
    )
    if (
        session_record is not None
        and session_record.revoked_at is None
        and not is_expired(session_record.expires_at)
    ):
        session_record.revoked_at = datetime.now(timezone.utc)
    db.add(
        _audit(
            action="user.logout",
            resource_type="user",
            resource_id=user.id,
            request_id=request.state.request_id,
            actor_id=user.id,
            reason="session_revoked",
        )
    )
    db.commit()
    response.delete_cookie(
        settings.session_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite="lax",
    )
    response.delete_cookie(
        settings.csrf_cookie_name,
        path="/",
        secure=settings.session_cookie_secure,
        httponly=False,
        samesite="strict",
    )
    response.status_code = 204
    return response
