"""Seed a second membership in the disposable database used by the browser suite.

This helper is only invoked by the Stage 4 E2E test. It is not an API route and is
never run by the application process.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.config import get_settings  # noqa: E402
from app.db import build_engine, build_session_factory  # noqa: E402
from app.models import User, Workspace, WorkspaceMembership  # noqa: E402


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: seed_second_workspace.py <registered-email>", file=sys.stderr)
        return 2

    settings = get_settings()
    engine = build_engine(settings.database_url)
    session_factory = build_session_factory(engine)
    try:
        with session_factory() as session:
            user = session.scalar(select(User).where(User.email == sys.argv[1].lower()))
            if user is None:
                print("The browser test user was not found.", file=sys.stderr)
                return 1

            workspace_name = "Stage 4 Secondary E2E Workspace"
            workspace = session.scalar(
                select(Workspace).where(Workspace.name == workspace_name)
            )
            if workspace is None:
                workspace = Workspace(
                    name=workspace_name,
                    created_at=datetime.now(timezone.utc) + timedelta(seconds=5),
                )
                session.add(workspace)
                session.flush()

            membership = session.get(WorkspaceMembership, (user.id, workspace.id))
            if membership is None:
                session.add(
                    WorkspaceMembership(
                        user_id=user.id,
                        workspace_id=workspace.id,
                        role="member",
                    )
                )
            session.commit()
    finally:
        engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())