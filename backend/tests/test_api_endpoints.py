from backend.app.db.models import AnalysisRun, Evidence, Finding, PullRequest


def test_health_check(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_repository_crud(client, tenant_fixture):
    token = tenant_fixture["token_a"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a repository
    create_payload = {
        "full_name": "tenant-a/service-new",
        "default_branch": "main",
        "clone_url": "https://github.com/tenant-a/service-new.git",
        "is_private": False,
    }
    resp = client.post("/api/v1/repositories", json=create_payload, headers=headers)
    assert resp.status_code == 201
    created = resp.json()
    repo_id = created["id"]
    assert created["full_name"] == "tenant-a/service-new"

    # 2. Get repository by ID
    get_resp = client.get(f"/api/v1/repositories/{repo_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == repo_id

    # 3. Update repository
    patch_resp = client.patch(
        f"/api/v1/repositories/{repo_id}",
        json={"default_branch": "develop"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["default_branch"] == "develop"

    # 4. Delete repository
    del_resp = client.delete(f"/api/v1/repositories/{repo_id}", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "deleted"


def test_findings_resolution_lifecycle(client, tenant_fixture, db_session):
    token = tenant_fixture["token_a"]
    repo_a = tenant_fixture["repo_a"]
    org_a = tenant_fixture["org_a"]
    headers = {"Authorization": f"Bearer {token}"}

    # Seed an analysis run and finding
    pr = PullRequest(
        repository_id=repo_a.id,
        pr_number=99,
        title="feat: test PR",
        state="open",
        author_username="alice",
        base_ref="main",
        base_sha="sha1",
        head_ref="feat/branch",
        head_sha="sha2",
        html_url="https://github.com/tenant-a/service-alpha/pull/99",
    )
    db_session.add(pr)
    db_session.flush()

    run = AnalysisRun(
        organization_id=org_a.id,
        repository_id=repo_a.id,
        pull_request_id=pr.id,
        trigger_type="test",
        status="completed",
        base_sha="sha1",
        head_sha="sha2",
        merge_base_sha="sha1",
        tool_version="0.2.0",
        duration_ms=150,
        summary={"drift": 1},
    )
    db_session.add(run)
    db_session.flush()

    finding = Finding(
        analysis_run_id=run.id,
        finding_external_id="DCS-001",
        status="DRIFT",
        resolution_status="open",
        severity="high",
        rule_id="RULE_PARAM_DEFAULT_CHANGED",
        category="signature_drift",
        title="Parameter timeout updated",
        explanation="Default timeout changed from 30 to 60.",
        confidence=1.0,
        verification="deterministic",
        suggested_action="Update doc.",
    )
    db_session.add(finding)
    db_session.flush()

    ev = Evidence(
        finding_id=finding.id,
        evidence_external_id="EV-1",
        role="documentation",
        path="README.md",
        line_start=10,
        line_end=12,
        quote="Timeout default is 30.",
        source_kind="doc_span",
    )
    db_session.add(ev)
    db_session.commit()

    # 1. Fetch finding
    f_resp = client.get(f"/api/v1/findings/{finding.id}", headers=headers)
    assert f_resp.status_code == 200
    f_data = f_resp.json()
    assert f_data["resolution_status"] == "open"
    assert len(f_data["evidence"]) == 1

    # 2. Update status to acknowledged
    patch_resp = client.patch(
        f"/api/v1/findings/{finding.id}/status",
        json={"resolution_status": "acknowledged", "resolution_reason": "Will fix next week"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["resolution_status"] == "acknowledged"
    assert updated["resolution_reason"] == "Will fix next week"


def test_webhook_deduplication(client):
    headers = {
        "X-GitHub-Delivery": "delivery-unique-12345",
        "X-GitHub-Event": "ping",
    }
    payload = {"zen": "Keep it logically awesome."}

    # First delivery: accepted
    resp1 = client.post("/api/v1/webhooks/github", json=payload, headers=headers)
    assert resp1.status_code == 202
    assert resp1.json()["status"] == "accepted"

    # Second delivery with same delivery ID: rejected with 409 Conflict
    resp2 = client.post("/api/v1/webhooks/github", json=payload, headers=headers)
    assert resp2.status_code == 409
    assert "Duplicate webhook delivery" in resp2.json()["detail"]
