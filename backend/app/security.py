"""Password hashing and opaque server-side session helpers."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.config import Settings
from app.models import UserSession

_password_hasher = PasswordHasher()
_dummy_password_hash = _password_hasher.hash(secrets.token_urlsafe(24))


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, encoded_hash: str | None) -> bool:
    candidate = encoded_hash or _dummy_password_hash
    try:
        valid = _password_hasher.verify(candidate, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        valid = False
    return bool(valid and encoded_hash)


def hash_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_session(user_id: str, settings: Settings) -> tuple[str, str, UserSession]:
    raw_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc)
    session = UserSession(
        user_id=user_id,
        token_hash=hash_session_token(raw_token),
        csrf_token_hash=hash_session_token(csrf_token),
        expires_at=now + timedelta(hours=settings.session_ttl_hours),
    )
    return raw_token, csrf_token, session


def is_expired(value: datetime, *, now: datetime | None = None) -> bool:
    current = now or datetime.now(timezone.utc)
    # SQLite may return naive datetimes even for timezone-aware columns.
    normalized = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value
    return normalized <= current
