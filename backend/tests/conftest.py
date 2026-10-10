import os

import pytest
from collections.abc import Iterator

from fastapi.testclient import TestClient

from app.config import Settings
from app.db import Base, build_engine, build_session_factory
from app.main import create_app


@pytest.fixture
def client(tmp_path) -> Iterator[TestClient]:
    # The PostgreSQL API suite uses a dedicated disposable database. Its schema
    # is reset per test; the separate migration database remains untouched.
    database_url = os.environ.get("NEXORION_API_TEST_DATABASE_URL")
    if not database_url:
        database_url = f"sqlite:///{tmp_path / 'nexorion-test.db'}"
    settings = Settings(
        app_env="test",
        database_url=database_url,
        session_cookie_secure=False,
        allow_self_registration=True,
    )
    engine = build_engine(database_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    session_factory = build_session_factory(engine)
    application = create_app(settings=settings, session_factory=session_factory)
    with TestClient(application) as test_client:
        yield test_client
    engine.dispose()
