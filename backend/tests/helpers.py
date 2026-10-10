from uuid import uuid4

from fastapi.testclient import TestClient

from app.models import WorkspaceMembership


def register(client: TestClient, email: str = "owner@example.com") -> dict:
    response = client.post(
        "/v1/auth/register",
        json={
            "email": email,
            "password": "A sufficiently long test password 123!",
            "workspace_name": "Research Workspace",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def mission_payload() -> dict:
    return {
        "objective": "Investigate synthetic authentication failure events",
        "scope": {
            "mode": "synthetic_only",
            "scenario_ids": ["scenario-auth-failure-v1"],
            "entity_ids": ["entity-auth-service-001"],
            "excluded_targets": ["all external systems", "all real credentials"],
        },
        "autonomy_tier": "observe_explain",
    }


def csrf_headers(client: TestClient, workspace_id: str | None = None) -> dict[str, str]:
    token = client.cookies.get("nexorion_csrf")
    assert token
    headers = {"X-CSRF-Token": token}
    if workspace_id:
        headers["X-Workspace-ID"] = workspace_id
    return headers


def prepare_approved_job(
    client: TestClient, workspace_id: str, mission_id: str,
    scenario_id: str, idempotency_key: str,
) -> dict:
    """Drive the public lifecycle and obtain a distinct owner approval for a test run."""
    requester = client.get("/v1/auth/me")
    assert requester.status_code == 200, requester.text
    requester_email = requester.json()["user"]["email"]
    password = "A sufficiently long test password 123!"

    mission_response = client.get(
        f"/v1/missions/{mission_id}", headers={"X-Workspace-ID": workspace_id},
    )
    assert mission_response.status_code == 200, mission_response.text
    mission = mission_response.json()
    for command in ("validate", "validation_passed", "begin_planning", "plan_ready"):
        response = client.post(
            f"/v1/missions/{mission_id}/commands",
            headers=csrf_headers(client, workspace_id),
            json={
                "command": command, "expected_version": mission["version"],
                "reason": "automated Stage 5 acceptance test",
            },
        )
        assert response.status_code == 200, response.text
        mission = response.json()

    approver_email = f"stage5-approver-{uuid4().hex}@example.test"
    approver = register(client, approver_email)
    db = client.app.state.session_factory()
    try:
        db.add(WorkspaceMembership(
            user_id=approver["user"]["id"], workspace_id=workspace_id, role="owner",
        ))
        db.commit()
    finally:
        db.close()

    approval = client.post(
        f"/v1/missions/{mission_id}/approvals",
        headers=csrf_headers(client, workspace_id),
        json={
            "decision": "approved", "reason": "distinct owner approved synthetic test",
            "expires_in_minutes": 15,
        },
    )
    assert approval.status_code == 201, approval.text

    login = client.post("/v1/auth/login", json={
        "email": requester_email, "password": password,
    })
    assert login.status_code == 200, login.text
    queued = client.post(
        f"/v1/missions/{mission_id}/jobs",
        headers={**csrf_headers(client, workspace_id), "Idempotency-Key": idempotency_key},
        json={"scenario_id": scenario_id, "idempotency_key": idempotency_key},
    )
    assert queued.status_code == 201, queued.text
    return queued.json()
