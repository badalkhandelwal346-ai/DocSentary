# DocSentry — Security & Multi-Tenancy Architecture
**Version:** 0.2.0-sec  
**Standard:** Enterprise Security & Defense-in-Depth

---

## 1. Zero Untrusted Code Execution (Core Security Principle)

DocSentry processes untrusted codebases submitted via pull requests. Traditional static analysis or documentation generators often execute code (e.g. `import my_module`, running `sphinx-build`, or invoking `setup.py`), which creates remote code execution (RCE) vulnerabilities.

**DocSentry strictly prohibits executing repository code:**
1. **Pure AST Extraction:** DocSentry parses Python code using `ast.parse()` inside Python's native parser without importing or executing bytecode.
2. **Read-Only Git Snapshots:** Files are inspected directly from git blob objects (`git show <sha>:<path>`) or diff hunks (`git diff`).
3. **No Dynamic Runtime Introspection:** Symbols, signatures, and default values are extracted statically from syntax tree nodes (`ast.FunctionDef`, `ast.Constant`, `ast.Assign`).

---

## 2. Multi-Tenancy & Data Isolation

Multi-tenancy isolation is enforced at every layer:

```
+-------------------------------------------------------------+
| 1. HTTP API Layer                                           |
|    - JWT token decoded to authenticate User                |
|    - Organization membership verified from DB               |
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
| 2. Dependency Injection Guard (FastAPI)                     |
|    - `get_current_tenant_org()` enforces active org         |
|    - Rejects cross-tenant header tampering with 403 Forbidden|
+-------------------------------------------------------------+
                              |
+-------------------------------------------------------------+
| 3. Repository & Query Layer (SQLAlchemy)                    |
|    - Explicit `where(Organization.id == tenant_id)` in all  |
|      repo, PR, analysis, and finding lookups                |
|    - Direct ID spoofing (e.g. GET /repos/OTHER_ORG_REPO)   |
|      returns 404 Not Found                                  |
+-------------------------------------------------------------+
```

### Direct Access Spoofing Protection Test Pattern
```python
def test_cross_tenant_access_forbidden(client, tenant_a_auth, tenant_b_repo_id):
    # Attempting to access Tenant B's repository with Tenant A's token
    response = client.get(
        f"/api/v1/repositories/{tenant_b_repo_id}",
        headers={"Authorization": f"Bearer {tenant_a_auth['token']}"}
    )
    # Must fail with 404 (or 403) to prevent ID enumeration
    assert response.status_code == 404
```

---

## 3. Authentication & Session Management

1. **JWT Standard:** Tokens are signed using HMAC-SHA256 with a strong secret key (`DOCSENTRY_SECRET_KEY`).
2. **Claims Structure:**
   ```json
   {
     "sub": "u_8a7d1e3f-6b2c-4f9e-9d8a-7e1f3a5b6c7d",
     "org_id": "org_9c8b7a6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
     "username": "octocat",
     "exp": 1793500000,
     "iat": 1793413600
   }
   ```
3. **Password Security:** If local credentials are used, passwords are encrypted using `bcrypt` with work factor 12.

---

## 4. Webhook Security & Tamper Resistance

1. **HMAC SHA-256 Signatures:** Inbound GitHub webhooks require validation against `DOCSENTRY_GITHUB_WEBHOOK_SECRET` via `hmac.compare_digest`. Payloads failing validation are dropped with HTTP 401.
2. **Replay Attack Mitigation:** Every webhook delivery ID (`X-GitHub-Delivery`) is recorded in the `webhook_events` table with a unique constraint. Replayed requests are rejected with HTTP 409 Conflict.
3. **Short-Lived Secrets:** Private keys used for GitHub App JWT generation are kept in environment variables or cloud secret managers and are never written to disk or database tables.

---

## 5. Audit Logging

Every state-altering event (creating an analysis run, dismissing a drift finding, modifying repository settings, connecting GitHub App) is written synchronously to `audit_logs` capturing:
- Actor (`user_id` or `system`)
- Scoped `organization_id`
- Timestamp and client IP address
- Action name and affected entity ID
- Detailed before/after diff in JSON
