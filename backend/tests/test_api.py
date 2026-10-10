from fastapi.testclient import TestClient

from tests.helpers import csrf_headers, mission_payload, register


def test_register_sets_server_side_session_and_workspace(client: TestClient) -> None:
    response = client.post(
        "/v1/auth/register",
        json={
            "email": "owner@example.com",
            "password": "A sufficiently long test password 123!",
            "workspace_name": "Research Workspace",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "owner@example.com"
    assert len(body["workspaces"]) == 1
    assert body["workspaces"][0]["role"] == "owner"
    assert client.cookies.get("nexorion_session")
    assert "nexorion_session" not in str(body)
    cookie_headers = [value.lower() for value in response.headers.get_list("set-cookie")]
    session_header = next(
        value for value in cookie_headers if value.startswith("nexorion_session=")
    )
    csrf_header = next(value for value in cookie_headers if value.startswith("nexorion_csrf="))
    assert "httponly" in session_header and "samesite=lax" in session_header
    assert "httponly" not in csrf_header and "samesite=strict" in csrf_header


def test_authenticated_user_can_create_list_and_read_draft_mission(client: TestClient) -> None:
    body = register(client)
    workspace_id = body["workspaces"][0]["id"]
    created = client.post(
        "/v1/missions",
        headers=csrf_headers(client, workspace_id),
        json=mission_payload(),
    )
    assert created.status_code == 201, created.text
    mission = created.json()
    assert mission["workspace_id"] == workspace_id
    assert mission["state"] == "draft"
    assert mission["scope"]["mode"] == "synthetic_only"
    listed = client.get("/v1/missions", headers={"X-Workspace-ID": workspace_id})
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [mission["id"]]
    loaded = client.get(
        f"/v1/missions/{mission['id']}", headers={"X-Workspace-ID": workspace_id}
    )
    assert loaded.status_code == 200
    assert loaded.json()["id"] == mission["id"]


def test_login_uses_server_side_session_and_generic_credentials_error(client: TestClient) -> None:
    register(client, "login@example.com")
    client.cookies.clear()
    invalid = client.post(
        "/v1/auth/login",
        json={"email": "login@example.com", "password": "not-the-right-password"},
    )
    assert invalid.status_code == 401
    assert invalid.json()["error"]["code"] == "INVALID_CREDENTIALS"
    valid = client.post(
        "/v1/auth/login",
        json={"email": "login@example.com", "password": "A sufficiently long test password 123!"},
    )
    assert valid.status_code == 200
    assert client.get("/v1/auth/me").status_code == 200


def test_duplicate_registration_is_rejected(client: TestClient) -> None:
    register(client, "duplicate@example.com")
    duplicate = client.post(
        "/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "A sufficiently long test password 123!",
        },
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "ACCOUNT_ALREADY_EXISTS"


def test_workspace_boundary_hides_another_users_mission(client: TestClient) -> None:
    first = register(client, "first@example.com")
    first_workspace = first["workspaces"][0]["id"]
    created = client.post(
        "/v1/missions",
        headers=csrf_headers(client, first_workspace),
        json=mission_payload(),
    )
    assert created.status_code == 201
    mission_id = created.json()["id"]
    with TestClient(client.app) as second_client:
        second = register(second_client, "second@example.com")
        second_workspace = second["workspaces"][0]["id"]
        denied = second_client.get(
            f"/v1/missions/{mission_id}", headers={"X-Workspace-ID": second_workspace}
        )
        assert denied.status_code == 404
        assert denied.json()["error"]["code"] == "MISSION_NOT_FOUND"


def test_csrf_is_required_for_mutation(client: TestClient) -> None:
    body = register(client)
    response = client.post(
        "/v1/missions",
        headers={"X-Workspace-ID": body["workspaces"][0]["id"]},
        json=mission_payload(),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"


def test_live_or_observed_scope_is_rejected_and_errors_have_request_id(client: TestClient) -> None:
    body = register(client)
    payload = mission_payload()
    payload["scope"]["mode"] = "observed"
    response = client.post(
        "/v1/missions",
        headers={
            **csrf_headers(client, body["workspaces"][0]["id"]),
            "X-Request-ID": "stage2-test-01",
        },
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_FAILED"
    assert response.json()["request_id"] == "stage2-test-01"
    assert response.headers["X-Request-ID"] == "stage2-test-01"


def test_client_cannot_choose_mission_state(client: TestClient) -> None:
    body = register(client)
    payload = mission_payload()
    payload["state"] = "succeeded"
    response = client.post(
        "/v1/missions",
        headers=csrf_headers(client, body["workspaces"][0]["id"]),
        json=payload,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "REQUEST_VALIDATION_FAILED"


def test_logout_revokes_session(client: TestClient) -> None:
    register(client)
    assert client.get("/v1/auth/me").status_code == 200
    logout = client.post("/v1/auth/logout", headers=csrf_headers(client))
    assert logout.status_code == 204
    assert client.get("/v1/auth/me").status_code == 401


def test_health_and_readiness_are_separate(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}
    assert client.get("/v1/health").json() == {"status": "ok"}
    assert client.get("/v1/ready").json() == {"status": "ready"}


def test_csrf_cookie_must_match_server_side_session_hash(client: TestClient) -> None:
    body = register(client)
    workspace_id = body["workspaces"][0]["id"]
    raw_session = client.cookies.get("nexorion_session")
    assert raw_session
    forged_csrf = "attacker-controlled-csrf-token"
    response = client.post(
        "/v1/missions",
        headers={
            "Cookie": f"nexorion_session={raw_session}; nexorion_csrf={forged_csrf}",
            "X-CSRF-Token": forged_csrf,
            "X-Workspace-ID": workspace_id,
        },
        json=mission_payload(),
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "CSRF_VALIDATION_FAILED"


def test_validation_error_does_not_echo_submitted_values(client: TestClient) -> None:
    response = client.post(
        "/v1/auth/register",
        json={"email": "not-an-email", "password": "short-secret"},
    )
    assert response.status_code == 422
    assert "not-an-email" not in response.text
    assert "short-secret" not in response.text


def test_production_settings_fail_closed_without_required_controls() -> None:
    import pytest
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            database_url="postgresql+psycopg://app:secret@localhost/nexorion",
            session_cookie_secure=False,
            allow_self_registration=False,
        )
    with pytest.raises(ValidationError):
        Settings(
            app_env="production",
            database_url="postgresql+psycopg://app:secret@localhost/nexorion",
            session_cookie_secure=True,
            allow_self_registration=True,
        )
