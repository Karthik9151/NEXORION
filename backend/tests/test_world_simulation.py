from fastapi.testclient import TestClient

from app.simulation import SCENARIO_REGISTRY, evaluate_fixture, get_fixture, verify_fixture_result
from tests.helpers import csrf_headers, mission_payload, register


def _create_simulation_mission(client: TestClient, workspace_id: str,
    scenario_id: str = "scenario-auth-failure-v1") -> str:
    payload = mission_payload()
    payload["autonomy_tier"] = "simulate_synthetic"
    payload["scope"]["scenario_ids"] = [scenario_id]
    payload["scope"]["entity_ids"] = []
    response = client.post(
        "/v1/missions",
        headers=csrf_headers(client, workspace_id),
        json=payload,
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _create_entity(client: TestClient, workspace_id: str, name: str) -> dict:
    response = client.post(
        "/v1/world/entities",
        headers=csrf_headers(client, workspace_id),
        json={
            "entity_type": "service",
            "name": name,
            "environment_id": "synthetic-lab",
            "attributes": {"purpose": "test fixture", "criticality": "medium"},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_digital_world_entities_and_relationships_are_workspace_scoped(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    first = _create_entity(client, workspace_id, "Synthetic Auth Service")
    second = _create_entity(client, workspace_id, "Synthetic Event Store")

    relationship = client.post(
        "/v1/world/relationships",
        headers=csrf_headers(client, workspace_id),
        json={
            "from_entity_id": first["id"],
            "to_entity_id": second["id"],
            "relationship_type": "emits",
        },
    )
    assert relationship.status_code == 201, relationship.text
    assert relationship.json()["source_class"] == "synthetic"

    listed = client.get("/v1/world/entities", headers={"X-Workspace-ID": workspace_id})
    assert listed.status_code == 200
    assert {item["id"] for item in listed.json()} == {first["id"], second["id"]}

    relationships = client.get("/v1/world/relationships", headers={"X-Workspace-ID": workspace_id})
    assert relationships.status_code == 200
    assert len(relationships.json()) == 1

    with TestClient(client.app) as other_client:
        other = register(other_client, "other@example.com")
        other_workspace = other["workspaces"][0]["id"]
        invisible = other_client.get(
            "/v1/world/entities", headers={"X-Workspace-ID": other_workspace}
        )
        assert invisible.status_code == 200
        assert invisible.json() == []


def test_world_attributes_reject_secret_like_keys(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    response = client.post(
        "/v1/world/entities",
        headers=csrf_headers(client, workspace_id),
        json={
            "entity_type": "identity",
            "name": "Synthetic Identity",
            "attributes": {"access_token": "never-store-this"},
        },
    )
    assert response.status_code == 422
    assert "never-store-this" not in response.text


def test_relationship_cannot_cross_workspace_boundary(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    first = _create_entity(client, workspace_id, "Owned Entity")
    with TestClient(client.app) as other_client:
        other = register(other_client, "other-link@example.com")
        other_workspace = other["workspaces"][0]["id"]
        second = _create_entity(other_client, other_workspace, "Other Workspace Entity")
        response = client.post(
            "/v1/world/relationships",
            headers=csrf_headers(client, workspace_id),
            json={
                "from_entity_id": first["id"],
                "to_entity_id": second["id"],
                "relationship_type": "depends_on",
            },
        )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "WORLD_ENTITY_NOT_FOUND"


def test_baseline_is_versioned_and_digest_is_stable(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    _create_entity(client, workspace_id, "Synthetic Auth Service")
    mission_id = _create_simulation_mission(client, workspace_id)

    first = client.post(
        f"/v1/missions/{mission_id}/baselines",
        headers=csrf_headers(client, workspace_id),
    )
    second = client.post(
        f"/v1/missions/{mission_id}/baselines",
        headers=csrf_headers(client, workspace_id),
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["sequence"] == 1
    assert second.json()["sequence"] == 2
    assert first.json()["graph_digest"] == second.json()["graph_digest"]
    assert first.json()["entity_count"] == 1
    listed = client.get(
        f"/v1/missions/{mission_id}/baselines",
        headers={"X-Workspace-ID": workspace_id},
    )
    assert [item["sequence"] for item in listed.json()] == [1, 2]


def test_simulation_requires_tier_and_baseline(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    payload = mission_payload()
    payload["scope"]["entity_ids"] = []
    mission = client.post(
        "/v1/missions",
        headers=csrf_headers(client, workspace_id),
        json=payload,
    )
    mission_id = mission.json()["id"]
    rejected = client.post(
        f"/v1/missions/{mission_id}/simulate",
        headers={
            **csrf_headers(client, workspace_id),
            "Idempotency-Key": "stage3-test-key-001",
        },
        json={"scenario_id": "scenario-auth-failure-v1"},
    )
    assert rejected.status_code == 403
    assert rejected.json()["error"]["code"] == "SIMULATION_TIER_REQUIRED"

    simulation_mission_id = _create_simulation_mission(client, workspace_id)
    missing_baseline = client.post(
        f"/v1/missions/{simulation_mission_id}/simulate",
        headers={
            **csrf_headers(client, workspace_id),
            "Idempotency-Key": "stage3-test-key-002",
        },
        json={"scenario_id": "scenario-auth-failure-v1"},
    )
    assert missing_baseline.status_code == 409
    assert missing_baseline.json()["error"]["code"] == "BASELINE_REQUIRED"


def test_synthetic_simulation_is_reproducible_evidenced_and_idempotent(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    mission_id = _create_simulation_mission(client, workspace_id)
    baseline = client.post(
        f"/v1/missions/{mission_id}/baselines",
        headers=csrf_headers(client, workspace_id),
    )
    assert baseline.status_code == 201, baseline.text

    headers = {
        **csrf_headers(client, workspace_id),
        "Idempotency-Key": "stage3-repeatable-run-001",
    }
    response = client.post(
        f"/v1/missions/{mission_id}/simulate",
        headers=headers,
        json={"scenario_id": "scenario-auth-failure-v1"},
    )
    assert response.status_code == 201, response.text
    run = response.json()
    assert run["status"] == "completed"
    assert run["outcome"] == "suspicious_auth_pattern"
    assert run["baseline_id"] == baseline.json()["id"]
    assert run["input_digest"] and run["output_digest"]
    assert run["result"]["source_class"] == "synthetic"
    # Fixture consistency is explicitly not the Origo verification status.
    assert "verification" not in run["result"]
    assert all(check["passed"] for check in run["result"]["fixture_consistency"]["checks"])
    assert run["evidence"][0]["source_class"] == "synthetic"
    assert run["evidence"][0]["content_digest"]
    assert run["evidence"][0]["payload"]["supporting_event_ids"] == [
        "E1", "E2", "E3", "E4", "E5", "E6"
    ]
    assert run["evidence"][0]["payload"]["payload_schema_version"] == "1.0"
    assert len(run["evidence"][0]["payload"]["events"]) == 6
    assert run["result"]["fixture_consistency"]["scope"] == "deterministic fixture assertions only"

    repeated = client.post(
        f"/v1/missions/{mission_id}/simulate",
        headers=headers,
        json={"scenario_id": "scenario-auth-failure-v1"},
    )
    assert repeated.status_code == 201
    assert repeated.json()["id"] == run["id"]
    assert repeated.json()["output_digest"] == run["output_digest"]

    mission = client.get(
        f"/v1/missions/{mission_id}", headers={"X-Workspace-ID": workspace_id}
    )
    assert mission.json()["state"] == "succeeded"

    listed = client.get(
        f"/v1/missions/{mission_id}/runs", headers={"X-Workspace-ID": workspace_id}
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_simulation_scope_and_idempotency_key_are_enforced(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    mission_id = _create_simulation_mission(client, workspace_id)
    client.post(
        f"/v1/missions/{mission_id}/baselines",
        headers=csrf_headers(client, workspace_id),
    )
    bad_key = client.post(
        f"/v1/missions/{mission_id}/simulate",
        headers={**csrf_headers(client, workspace_id), "Idempotency-Key": "short"},
        json={"scenario_id": "scenario-auth-failure-v1"},
    )
    assert bad_key.status_code == 400
    assert bad_key.json()["error"]["code"] == "IDEMPOTENCY_KEY_REQUIRED"

    out_of_scope = client.post(
        f"/v1/missions/{mission_id}/simulate",
        headers={
            **csrf_headers(client, workspace_id),
            "Idempotency-Key": "stage3-out-of-scope-run-001",
        },
        json={"scenario_id": "scenario-auth-benign-control-v1"},
    )
    assert out_of_scope.status_code == 403
    assert out_of_scope.json()["error"]["code"] == "SCENARIO_OUT_OF_SCOPE"


def test_registered_benign_control_does_not_raise_suspicious_success_finding() -> None:
    scenario_id = "scenario-auth-benign-control-v1"
    fixture = get_fixture(scenario_id)
    assert fixture is not None
    result = evaluate_fixture(scenario_id, fixture)
    verification = verify_fixture_result(scenario_id, fixture, result)
    assert result["outcome"] == "repeated_auth_failures"
    assert result["outcome"] != "suspicious_auth_pattern"
    assert verification["status"] == "verified"
    assert len(SCENARIO_REGISTRY) == 2
