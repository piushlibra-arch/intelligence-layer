from datetime import datetime, timezone
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_and_readiness(client: AsyncClient):
    res = await client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["synthetic_data_only"] is True

    res2 = await client.get("/api/v1/readiness")
    assert res2.status_code == 200
    assert res2.json()["status"] == "ready"

@pytest.mark.asyncio
async def test_scenarios_and_replay_flow(client: AsyncClient):
    # 1. List scenarios
    res = await client.get("/api/v1/scenarios")
    assert res.status_code == 200
    scenarios = res.json()
    assert len(scenarios) >= 5
    scenario_ids = [s["id"] for s in scenarios]
    assert "scenario_a" in scenario_ids
    assert "scenario_b" in scenario_ids

    # 2. Replay scenario_b (Escalating risk)
    headers = {"X-API-Key": "test-api-key-12345"}
    replay_res = await client.post("/api/v1/scenarios/scenario_b/replay", headers=headers)
    assert replay_res.status_code == 200
    replay_data = replay_res.json()
    session_id = replay_data["session_id"]
    events = replay_data["events"]
    assert len(events) >= 10

    # 3. Ingest first 3 events
    for ev in events[:3]:
        ingest_res = await client.post(f"/api/v1/sessions/{session_id}/events", json=ev, headers=headers)
        assert ingest_res.status_code == 200
        assert ingest_res.json()["is_duplicate"] is False

    # 4. Ingest duplicate event (re-send event 0)
    dup_res = await client.post(f"/api/v1/sessions/{session_id}/events", json=events[0], headers=headers)
    assert dup_res.status_code == 200
    assert dup_res.json()["is_duplicate"] is True

    # 5. Check session state
    state_res = await client.get(f"/api/v1/sessions/{session_id}/state")
    assert state_res.status_code == 200
    state = state_res.json()
    assert state["events_processed"] == 3
    assert state["session"]["id"] == session_id

    # 6. Check audit records
    audit_res = await client.get("/api/v1/audit")
    assert audit_res.status_code == 200
    assert len(audit_res.json()) >= 3

@pytest.mark.asyncio
async def test_auth_protection_on_mutating_endpoints(client: AsyncClient):
    # Without X-API-Key should return 401
    res = await client.post("/api/v1/scenarios/scenario_a/replay")
    assert res.status_code == 401

    # With invalid key should return 401
    res2 = await client.post("/api/v1/scenarios/scenario_a/replay", headers={"X-API-Key": "wrong-key"})
    assert res2.status_code == 401
