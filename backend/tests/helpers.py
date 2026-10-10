from fastapi.testclient import TestClient


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
