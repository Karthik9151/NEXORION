"""Request-scoped database and authorization dependencies."""

import hmac
from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import ApiError
from app.models import User, UserSession, WorkspaceMembership
from app.security import hash_session_token, is_expired


def get_db(request: Request) -> Generator[Session, None, None]:
    db = request.app.state.session_factory()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    settings = request.app.state.settings
    raw_token = request.cookies.get(settings.session_cookie_name)
    if not raw_token:
        raise ApiError(401, "AUTHENTICATION_REQUIRED", "Authentication is required.")

    session_record = db.scalar(
        select(UserSession).where(UserSession.token_hash == hash_session_token(raw_token))
    )
    if (
        session_record is None
        or session_record.revoked_at is not None
        or is_expired(session_record.expires_at)
    ):
        raise ApiError(401, "SESSION_INVALID", "The session is invalid or has expired.")

    user = db.get(User, session_record.user_id)
    if user is None or not user.is_active:
        raise ApiError(401, "SESSION_INVALID", "The session is invalid or has expired.")
    return user


def require_csrf(request: Request, db: Session = Depends(get_db)) -> None:
    settings = request.app.state.settings
    raw_session_token = request.cookies.get(settings.session_cookie_name, "")
    cookie_token = request.cookies.get(settings.csrf_cookie_name, "")
    header_token = request.headers.get("x-csrf-token", "")
    if not cookie_token or not header_token or not hmac.compare_digest(cookie_token, header_token):
        raise ApiError(403, "CSRF_VALIDATION_FAILED", "A valid CSRF token is required.")

    session_record = db.scalar(
        select(UserSession).where(UserSession.token_hash == hash_session_token(raw_session_token))
    )
    if (
        session_record is None
        or session_record.revoked_at is not None
        or is_expired(session_record.expires_at)
        or not hmac.compare_digest(session_record.csrf_token_hash, hash_session_token(cookie_token))
    ):
        raise ApiError(403, "CSRF_VALIDATION_FAILED", "A valid CSRF token is required.")


def require_workspace_membership(
    db: Session,
    *,
    user_id: str,
    workspace_id: str | None,
) -> WorkspaceMembership:
    if not workspace_id or len(workspace_id) > 64:
        raise ApiError(400, "WORKSPACE_REQUIRED", "A valid X-Workspace-ID header is required.")
    membership = db.get(WorkspaceMembership, (user_id, workspace_id))
    if membership is None:
        # Use 404 to avoid revealing whether another workspace exists.
        raise ApiError(404, "WORKSPACE_NOT_FOUND", "The requested workspace was not found.")
    return membership
