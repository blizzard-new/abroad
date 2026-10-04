from test_calendar_task_scheduling import _authenticated_client


def test_workload_endpoint_and_workspace_roundtrip(tmp_path):
    client, headers = _authenticated_client(tmp_path)
    events = [dict(id="hours-task", title="準備讀書計畫", date="2026-10-09", effort_hours=4,
                   remaining_hours=2, preparation_days=7, depends_on=[], document_id="study-plan",
                   available_from="2026-10-05")]
    settings = dict(weekly_hours=6, weekdays=[1, 3, 5], horizon_days=30)
    response = client.post("/calendar/tasks/schedule", headers=headers,
                           json=dict(events=events, as_of="2026-10-05", availability=settings))
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    report = response.json()
    assert report["mode"] == "workload"
    assert report["work_sessions"][0]["hours"] == 2
    assert report["items"][0]["document_id"] == "study-plan"
    # Preview never changes the stored account workspace.
    before = client.get("/account/workspace", headers=headers).json()
    assert before["exists"] is False
    payload = before["workspace"]
    payload.update(deadline_events=events, planning_availability=settings)
    saved = client.put("/account/workspace", headers=headers, json=payload)
    assert saved.status_code == 200
    restored = client.get("/account/workspace", headers=headers).json()["workspace"]
    assert restored["planning_availability"] == settings
    assert restored["deadline_events"][0]["remaining_hours"] == 2
    assert restored["deadline_events"][0]["document_id"] == "study-plan"
    # A legacy client omitting the new settings must not clear them.
    restored.pop("planning_availability")
    for field in ("effort_hours", "remaining_hours", "depends_on", "available_from", "waiting_reason", "document_id"):
        restored["deadline_events"][0].pop(field)
    assert client.put("/account/workspace", headers=headers, json=restored).status_code == 200
    assert client.get("/account/workspace", headers=headers).json()["workspace"]["planning_availability"] == settings
    after = client.get("/account/workspace", headers=headers).json()["workspace"]
    assert after["deadline_events"][0]["remaining_hours"] == 2
    assert after["deadline_events"][0]["document_id"] == "study-plan"
    after["deadline_events"][0]["document_id"] = None
    after["deadline_events"][0]["remaining_hours"] = None
    assert client.put("/account/workspace", headers=headers, json=after).status_code == 200
    cleared = client.get("/account/workspace", headers=headers).json()["workspace"]
    assert cleared["deadline_events"][0]["document_id"] is None
    assert cleared["deadline_events"][0]["remaining_hours"] is None


def test_workload_mode_does_not_bypass_entitlements_or_accept_invalid_capacity(tmp_path, monkeypatch):
    client, headers = _authenticated_client(tmp_path)
    payload = dict(events=[], availability=dict(weekly_hours=6, weekdays=[0]))
    assert client.post("/calendar/tasks/schedule", headers=headers, json=payload).status_code == 422
    payload["availability"]["weekdays"] = [1]
    assert client.post("/calendar/tasks/schedule", json=payload).status_code == 401
    monkeypatch.setenv("EXCHANGE_PRODUCT_RELEASE_MODE", "public")
    assert client.post("/calendar/tasks/schedule", headers=headers, json=payload).status_code == 403
