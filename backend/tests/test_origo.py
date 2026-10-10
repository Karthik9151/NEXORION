from fastapi.testclient import TestClient

from app.models import EvidenceRecord, SimulationRun
from app.simulation import digest
from tests.helpers import csrf_headers, prepare_approved_job, register
from tests.test_world_simulation import _create_simulation_mission


def _completed_run(client: TestClient, workspace_id: str) -> tuple[str, dict]:
    mission_id = _create_simulation_mission(client, workspace_id)
    baseline = client.post(
        f"/v1/missions/{mission_id}/baselines",
        headers=csrf_headers(client, workspace_id),
    )
    assert baseline.status_code == 201, baseline.text
    prepare_approved_job(
        client, workspace_id, mission_id, "scenario-auth-failure-v1", "origo-test-run-001",
    )
    response = client.post(
        f"/v1/missions/{mission_id}/simulate",
        headers={**csrf_headers(client, workspace_id), "Idempotency-Key": "origo-test-run-001"},
        json={"scenario_id": "scenario-auth-failure-v1"},
    )
    assert response.status_code == 201, response.text
    return mission_id, response.json()


def test_simulation_does_not_claim_origo_verification_and_origo_persists_attempt(
    client: TestClient,
) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    mission_id, run = _completed_run(client, workspace_id)
    assert run["status"] == "completed"
    assert "verification" not in run["result"]
    assert run["evidence"][0]["payload"]["events"]

    headers = {**csrf_headers(client, workspace_id), "Idempotency-Key": "origo-test-attempt-001"}
    response = client.post(f"/v1/missions/{mission_id}/runs/{run['id']}/verify", headers=headers)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["status"] == "verified"
    assert body["verifier_version"]
    assert body["evidence_ids"] == [run["evidence"][0]["id"]]
    assert all(check["passed"] is True for check in body["checks"])

    repeated = client.post(f"/v1/missions/{mission_id}/runs/{run['id']}/verify", headers=headers)
    assert repeated.status_code == 200
    assert repeated.json()["id"] == body["id"]

    history = client.get(
        f"/v1/missions/{mission_id}/runs/{run['id']}/verification",
        headers={"X-Workspace-ID": workspace_id},
    )
    assert history.status_code == 200
    assert len(history.json()["items"]) == 1
    assert history.json()["latest"]["id"] == body["id"]


def test_legacy_evidence_without_events_is_inconclusive(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    mission_id, run = _completed_run(client, workspace_id)
    db = client.app.state.session_factory()
    try:
        evidence = db.get(EvidenceRecord, run["evidence"][0]["id"])
        assert evidence is not None
        evidence.payload = {
            "scenario_id": run["scenario_id"], "outcome": run["outcome"],
            "event_count": 6, "supporting_event_ids": ["E1", "E2"],
            "rule_set_version": run["rule_set_version"],
        }
        evidence.content_digest = digest(evidence.payload)
        db.commit()
    finally:
        db.close()

    response = client.post(
        f"/v1/missions/{mission_id}/runs/{run['id']}/verify",
        headers={
            **csrf_headers(client, workspace_id),
            "Idempotency-Key": "origo-legacy-attempt-001",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "inconclusive"


def test_tampered_evidence_fingerprint_fails_verification(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    mission_id, run = _completed_run(client, workspace_id)
    db = client.app.state.session_factory()
    try:
        evidence = db.get(EvidenceRecord, run["evidence"][0]["id"])
        assert evidence is not None
        evidence.content_digest = "0" * 64
        db.commit()
    finally:
        db.close()
    response = client.post(
        f"/v1/missions/{mission_id}/runs/{run['id']}/verify",
        headers={
            **csrf_headers(client, workspace_id),
            "Idempotency-Key": "origo-tamper-attempt-001",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "failed"


def test_conflicting_run_outcome_is_disputed(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    mission_id, run = _completed_run(client, workspace_id)
    db = client.app.state.session_factory()
    try:
        persisted = db.get(SimulationRun, run["id"])
        assert persisted is not None
        persisted.outcome = "repeated_auth_failures"
        db.commit()
    finally:
        db.close()
    response = client.post(
        f"/v1/missions/{mission_id}/runs/{run['id']}/verify",
        headers={
            **csrf_headers(client, workspace_id),
            "Idempotency-Key": "origo-dispute-attempt-001",
        },
    )
    assert response.status_code == 201
    assert response.json()["status"] == "disputed"
    assert response.json()["discrepancies"]


def test_reports_are_server_generated_and_workspace_scoped(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    mission_id, run = _completed_run(client, workspace_id)
    json_response = client.get(
        f"/v1/missions/{mission_id}/report", headers={"X-Workspace-ID": workspace_id},
    )
    assert json_response.status_code == 200
    report = json_response.json()
    assert report["scope"]["mission_id"] == mission_id
    assert report["runs"][0]["id"] == run["id"]
    assert report["runs"][0]["origo_verification"] is None

    markdown = client.get(
        f"/v1/missions/{mission_id}/report.md", headers={"X-Workspace-ID": workspace_id},
    )
    assert markdown.status_code == 200
    assert markdown.headers["content-type"].startswith("text/markdown")
    assert "NEXORION Synthetic Mission Research Report" in markdown.text
    assert "not requested" in markdown.text.lower()

    with TestClient(client.app) as other_client:
        other = register(other_client, "report-other@example.com")
        foreign = other_client.get(
            f"/v1/missions/{mission_id}/report",
            headers={"X-Workspace-ID": other["workspaces"][0]["id"]},
        )
        assert foreign.status_code == 404


def test_scenario_catalog_lists_only_registered_executable_scenarios(client: TestClient) -> None:
    register(client)
    response = client.get("/v1/scenarios")
    assert response.status_code == 200
    items = response.json()["items"]
    assert {item["id"] for item in items} == {
        "scenario-auth-failure-v1", "scenario-auth-benign-control-v1",
    }
    assert all(item["enabled"] is True for item in items)


def test_verification_requires_authentication_and_csrf(client: TestClient) -> None:
    owner = register(client)
    workspace_id = owner["workspaces"][0]["id"]
    mission_id, run = _completed_run(client, workspace_id)
    with TestClient(client.app) as anonymous:
        response = anonymous.post(
            f"/v1/missions/{mission_id}/runs/{run['id']}/verify",
            headers={"X-Workspace-ID": workspace_id},
        )
        assert response.status_code == 401
    denied = client.post(
        f"/v1/missions/{mission_id}/runs/{run['id']}/verify",
        headers={"X-Workspace-ID": workspace_id},
    )
    assert denied.status_code == 403
