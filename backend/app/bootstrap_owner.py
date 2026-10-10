"""One-time, fail-closed initial owner provisioning for a fresh deployment."""

import os

from sqlalchemy import func, select

from app.config import get_settings
from app.db import build_engine, build_session_factory
from app.models import AuditEvent, User, Workspace, WorkspaceMembership
from app.schemas import RegisterRequest
from app.security import hash_password


def main() -> None:
    """Create the first owner only when the database contains no users.

    Set NEXORION_BOOTSTRAP_OWNER_EMAIL and NEXORION_BOOTSTRAP_OWNER_PASSWORD
    for the first deployment. After the first owner is created, those secrets
    can be removed; future starts detect the existing user and do nothing.
    """
    settings = get_settings()
    engine = build_engine(settings.database_url)
    sessions = build_session_factory(engine)
    db = sessions()
    try:
        user_count = db.scalar(select(func.count()).select_from(User)) or 0
        if user_count:
            print("Initial owner bootstrap skipped: an account already exists.")
            return

        email = os.environ.get("NEXORION_BOOTSTRAP_OWNER_EMAIL", "").strip()
        password = os.environ.get("NEXORION_BOOTSTRAP_OWNER_PASSWORD", "")
        workspace_name = os.environ.get(
            "NEXORION_BOOTSTRAP_WORKSPACE_NAME", "NEXORION Workspace"
        )
        if not email or not password:
            raise SystemExit(
                "Fresh database has no users. Set NEXORION_BOOTSTRAP_OWNER_EMAIL and "
                "NEXORION_BOOTSTRAP_OWNER_PASSWORD before starting the service."
            )

        payload = RegisterRequest(
            email=email,
            password=password,
            workspace_name=workspace_name,
        )
        user = User(email=str(payload.email), password_hash=hash_password(payload.password))
        workspace = Workspace(name=payload.workspace_name or "NEXORION Workspace")
        db.add_all([user, workspace])
        db.flush()
        db.add(WorkspaceMembership(user_id=user.id, workspace_id=workspace.id, role="owner"))
        db.add(
            AuditEvent(
                actor_id=user.id,
                workspace_id=workspace.id,
                action="user.bootstrap_created",
                resource_type="user",
                resource_id=user.id,
                decision="allow",
                reason="initial_owner_bootstrap",
                request_id="bootstrap-owner",
            )
        )
        db.add(
            AuditEvent(
                actor_id=user.id,
                workspace_id=workspace.id,
                action="workspace.created",
                resource_type="workspace",
                resource_id=workspace.id,
                decision="allow",
                reason="initial_owner_bootstrap",
                request_id="bootstrap-owner",
            )
        )
        db.commit()
        print("Initial owner and workspace created successfully.")
    finally:
        db.close()
        engine.dispose()


if __name__ == "__main__":
    main()
