"""Seed a persisted, approved synthetic run for the browser Origo verification test.

Only the disposable E2E database is used. This script creates no API route and
never targets external systems.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "tests"))

from app.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402
from helpers import csrf_headers, mission_payload, prepare_approved_job, register  # noqa: E402


def main() -> int:
    email = f"origo-e2e-{uuid4().hex}@example.test"
    password = "A sufficiently long test password 123!"
    scenario_id = "scenario-auth-failure-v1"
    idempotency_key = f"origo-e2e-{uuid4().hex}"

    with TestClient(create_app(get_settings())) as client:
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
        prepare_approved_job(
            client, workspace_id, mission_id, scenario_id, idempotency_key
        )
        simulation = client.post(
            f"/v1/missions/{mission_id}/simulate",
            headers={
                **csrf_headers(client, workspace_id),
                "Idempotency-Key": idempotency_key,
            },
            json={"scenario_id": scenario_id},
        )
        assert simulation.status_code == 201, simulation.text
        run = simulation.json()
        assert run["status"] == "completed", run

    print(
        json.dumps(
            {
                "email": email,
                "password": password,
                "run_id": run["id"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
