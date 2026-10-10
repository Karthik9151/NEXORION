"""PostgreSQL-backed end-to-end smoke test, enabled only in the dedicated CI job."""

import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.db import build_engine, build_session_factory
from app.main import create_app
from tests.helpers import csrf_headers, prepare_approved_job


@pytest.mark.skipif(
    not os.environ.get("NEXORION_TEST_DATABASE_URL"),
    reason="set NEXORION_TEST_DATABASE_URL to run PostgreSQL integration",
)
def test_postgres_auth_mission_baseline_and_simulation_round_trip() -> None:
    database_url = os.environ["NEXORION_TEST_DATABASE_URL"]
    settings = Settings(
        app_env="test",
        database_url=database_url,
        session_cookie_secure=False,
        allow_self_registration=True,
    )
    engine = build_engine(database_url)
    application = create_app(
        settings=settings,
        session_factory=build_session_factory(engine),
    )

    try:
        with TestClient(application) as client:
            email = f"pg-{uuid4().hex}@example.com"
            registration = client.post(
                "/v1/auth/register",
                json={
                    "email": email,
                    "password": "A sufficiently long test password 123!",
                    "workspace_name": "PostgreSQL Integration Workspace",
                },
            )
            assert registration.status_code == 201, registration.text
            workspace_id = registration.json()["workspaces"][0]["id"]

            mission = client.post(
                "/v1/missions",
                headers=csrf_headers(client, workspace_id),
                json={
                    "objective": "Exercise the synthetic simulation path on PostgreSQL",
                    "scope": {
                        "mode": "synthetic_only",
                        "scenario_ids": ["scenario-auth-failure-v1"],
                        "entity_ids": [],
                        "excluded_targets": [
                            "all external systems",
                            "all real credentials",
                        ],
                    },
                    "autonomy_tier": "simulate_synthetic",
                },
            )
            assert mission.status_code == 201, mission.text
            mission_id = mission.json()["id"]

            baseline = client.post(
                f"/v1/missions/{mission_id}/baselines",
                headers=csrf_headers(client, workspace_id),
            )
            assert baseline.status_code == 201, baseline.text
            simulation_key = f"pg-integration-{uuid4().hex}"
            prepare_approved_job(
                client, workspace_id, mission_id, "scenario-auth-failure-v1", simulation_key,
            )

            simulation = client.post(
                f"/v1/missions/{mission_id}/simulate",
                headers={
                    **csrf_headers(client, workspace_id),
                    "Idempotency-Key": simulation_key,
                },
                json={"scenario_id": "scenario-auth-failure-v1"},
            )
            assert simulation.status_code == 201, simulation.text
            assert simulation.json()["status"] == "completed"
            assert simulation.json()["outcome"] == "suspicious_auth_pattern"
            assert simulation.json()["evidence"]
    finally:
        engine.dispose()
