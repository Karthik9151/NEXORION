"""Seed a persisted, approved synthetic run for the browser Origo verification test.

Only the disposable E2E database is used. This script creates no API route and
never targets external systems.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "tests"))

from app.config import get_settings  # noqa: E402
from app.db import build_engine, build_session_factory  # noqa: E402
from app.models import SimulationRun  # noqa: E402
from app.stage5_models import MissionJob  # noqa: E402
from app.main import create_app  # noqa: E402
from helpers import csrf_headers, mission_payload, prepare_approved_job, register  # noqa: E402


def main() -> int:
    # ".test" is a reserved special-use TLD rejected by email-validator.
    # This identity is test-only; the E2E flow never sends email.
    email = f"origo-e2e-{uuid4().hex}@example.com"
    password = "A sufficiently long test password 123!"
    scenario_id = "scenario-auth-failure-v1"
    idempotency_key = f"origo-e2e-{uuid4().hex}"

    # The seed process prepares an authorized job but deliberately disables its own
    # worker. The separately running browser-test API process must execute it.
    test_settings = get_settings().model_copy(update={"nexorion_worker_enabled": False})
    with TestClient(create_app(test_settings)) as client:
        owner = register(client, email)
        workspace_id = owner["workspaces"][0]["id"]
        payload = mission_payload()
        payload["autonomy_tier"] = "simulate_synthetic"
        payload["scope"]["scenario_ids"] = [scenario_id]
        payload["scope"]["entity_ids"] = []
        mission_response = client.post(
            "/v1/missions",
            headers=csrf_headers(client, workspace_id),
            json=payload,
        )
        assert mission_response.status_code == 201, mission_response.text
        mission_id = mission_response.json()["id"]

        baseline = client.post(
            f"/v1/missions/{mission_id}/baselines",
            headers=csrf_headers(client, workspace_id),
        )
        assert baseline.status_code == 201, baseline.text
        job = prepare_approved_job(
            client, workspace_id, mission_id, scenario_id, idempotency_key
        )

    # Wait for the API process's configured background worker to consume the
    # durable queue record. This makes the E2E test fail if the worker loop is
    # absent or not started; the seed process never calls /simulate itself.
    engine = build_engine(get_settings().database_url)
    sessions = build_session_factory(engine)
    run_id = None
    try:
        deadline = time.monotonic() + 20.0
        while time.monotonic() < deadline:
            with sessions() as session:
                stored_job = session.get(MissionJob, job["id"])
                run = session.scalar(select(SimulationRun).where(
                    SimulationRun.workspace_id == workspace_id,
                    SimulationRun.mission_id == mission_id,
                    SimulationRun.idempotency_key == idempotency_key,
                ))
                if run is not None:
                    assert stored_job is not None and stored_job.status == "succeeded"
                    run_id = run.id
                    break
                if stored_job is None or stored_job.status in {
                    "review_required", "uncertain", "failed", "cancelled",
                }:
                    raise AssertionError(
                        f"Background worker did not safely complete job {job['id']}: "
                        f"{None if stored_job is None else stored_job.status}"
                    )
            time.sleep(0.1)
        assert run_id is not None, (
            "The background worker did not persist a run within 20 seconds."
        )
    finally:
        engine.dispose()

    print(
        json.dumps(
            {
                "email": email,
                "password": password,
                "run_id": run_id,
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
