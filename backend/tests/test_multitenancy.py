def test_tenant_data_isolation_repositories(client, tenant_fixture):
    """
    Verify that an authenticated user from Tenant A can only list Tenant A's repositories
    and receives 404 when querying Tenant B's repository by ID.
    """
    token_a = tenant_fixture["token_a"]
    token_b = tenant_fixture["token_b"]
    repo_b = tenant_fixture["repo_b"]

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 1. Tenant A lists repositories -> should only see service-alpha
    resp_a = client.get("/api/v1/repositories", headers=headers_a)
    assert resp_a.status_code == 200
    repos_a = resp_a.json()
    assert len(repos_a) == 1
    assert repos_a[0]["full_name"] == "tenant-a/service-alpha"

    # 2. Tenant B lists repositories -> should only see service-beta
    resp_b = client.get("/api/v1/repositories", headers=headers_b)
    assert resp_b.status_code == 200
    repos_b = resp_b.json()
    assert len(repos_b) == 1
    assert repos_b[0]["full_name"] == "tenant-b/service-beta"

    # 3. Tenant A attempts to access Tenant B's repository by ID
    spoofed_get = client.get(f"/api/v1/repositories/{repo_b.id}", headers=headers_a)
    assert spoofed_get.status_code == 404, "Cross-tenant repository lookup must return 404"

    # 4. Tenant A attempts to delete Tenant B's repository by ID
    spoofed_delete = client.delete(f"/api/v1/repositories/{repo_b.id}", headers=headers_a)
    assert spoofed_delete.status_code == 404, "Cross-tenant repository deletion must return 404"

    # 5. Tenant A attempts to spoof X-Organization-Id header to Tenant B's org
    spoofed_header = client.get(
        "/api/v1/repositories",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Organization-Id": tenant_fixture["org_b"].id,
        },
    )
    assert (
        spoofed_header.status_code == 403
    ), "Tampering with X-Organization-Id must return 403 Forbidden"
