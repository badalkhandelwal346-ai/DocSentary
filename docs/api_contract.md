# DocSentry — REST API Specification & Contracts
**Version:** 0.2.0-api  
**Protocol:** HTTPS / JSON REST  
**OpenAPI Specification:** Hosted dynamically at `/api/v1/openapi.json` and `/docs`

---

## 1. Authentication & Common Headers

### Request Headers
| Header | Type | Description |
|---|---|---|
| `Authorization` | `Bearer <JWT_TOKEN>` | Bearer token for authenticated endpoints. |
| `Content-Type` | `application/json` | Required for all POST/PATCH/PUT requests. |
| `X-Organization-Id` | `UUID` (optional) | Explicitly selects tenant workspace if user belongs to multiple organizations. |

### Standard Error Response Format
All error responses return RFC 7807 compliant JSON:
```json
{
  "detail": "Error description message",
  "code": "ENTITY_NOT_FOUND",
  "errors": []
}
```

Standard Status Codes:
- `200 OK`: Request succeeded.
- `201 Created`: Resource created.
- `202 Accepted`: Asynchronous task queued.
- `400 Bad Request`: Validation failure.
- `401 Unauthorized`: Missing or invalid bearer token.
- `403 Forbidden`: Insufficient role or cross-organization access violation.
- `404 Not Found`: Resource does not exist or user lacks permission to view it.
- `409 Conflict`: Unique constraint violation (e.g. duplicate webhook delivery).
- `500 Internal Server Error`: Unhandled server exception.

---

## 2. API Endpoints

### 2.1 Authentication & Profile

#### `POST /api/v1/auth/github`
Exchange GitHub OAuth temporary code or personal access token for a DocSentry JWT session.

- **Request Body:**
```json
{
  "code": "gh_oauth_temp_code_12345",
  "redirect_uri": "http://localhost:5173/auth/callback"
}
```
- **Response `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "id": "u_8a7d1e3f-6b2c-4f9e-9d8a-7e1f3a5b6c7d",
    "email": "developer@example.com",
    "username": "octocat",
    "full_name": "The Octocat",
    "avatar_url": "https://avatars.githubusercontent.com/u/583231",
    "organization": {
      "id": "org_9c8b7a6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
      "slug": "octo-corp",
      "name": "OctoCorp"
    }
  }
}
```

#### `GET /api/v1/auth/me`
Retrieve currently authenticated user profile and active organization.
- **Headers:** `Authorization: Bearer <token>`
- **Response `200 OK`:** User entity schema above.

#### `POST /api/v1/auth/logout`
Revoke active session token.
- **Response `200 OK`:** `{"status": "logged_out"}`

---

### 2.2 Organizations & Activity

#### `GET /api/v1/organizations`
List organizations accessible by the current user.
- **Response `200 OK`:**
```json
[
  {
    "id": "org_9c8b7a6d-5e4f-3a2b-1c0d-9e8f7a6b5c4d",
    "slug": "octo-corp",
    "name": "OctoCorp",
    "avatar_url": null,
    "role": "owner",
    "created_at": "2026-10-31T20:00:00Z"
  }
]
```

#### `GET /api/v1/organizations/{id}/activity`
Get recent audit logs and drift scan events for the organization.
- **Query Params:** `limit` (default: 20), `offset` (default: 0)
- **Response `200 OK`:**
```json
{
  "items": [
    {
      "id": "aud_123",
      "action": "finding.resolved",
      "entity_type": "finding",
      "entity_id": "f_456",
      "user": {"username": "octocat"},
      "created_at": "2026-11-01T02:15:00Z"
    }
  ],
  "total": 1
}
```

---

### 2.3 Repositories

#### `GET /api/v1/repositories`
List connected repositories for the current organization.
- **Response `200 OK`:**
```json
[
  {
    "id": "repo_111",
    "github_repo_id": 98765432,
    "full_name": "Atharv386/DocSentary",
    "default_branch": "main",
    "is_private": false,
    "clone_url": "https://github.com/Atharv386/DocSentary.git",
    "is_active": true,
    "open_findings_count": 3,
    "active_prs_count": 2,
    "last_analysis_at": "2026-11-01T03:30:00Z",
    "created_at": "2026-10-31T20:10:00Z"
  }
]
```

#### `POST /api/v1/repositories`
Connect a new repository to DocSentry.
- **Request Body:**
```json
{
  "full_name": "Atharv386/DocSentary",
  "default_branch": "main",
  "clone_url": "https://github.com/Atharv386/DocSentary.git",
  "is_private": false
}
```
- **Response `201 Created`:** Repository schema.

#### `GET /api/v1/repositories/{id}`
Retrieve repository details, settings, and health status.
- **Response `200 OK`:** Full repository object.

#### `PATCH /api/v1/repositories/{id}`
Update repository configuration (e.g. docs globs, exclusions).
- **Request Body:**
```json
{
  "is_active": true,
  "config_override": {
    "docs_globs": ["docs/**/*.md", "README.md"],
    "exclude_globs": ["tests/**", "vendor/**"]
  }
}
```
- **Response `200 OK`:** Updated repository object.

#### `DELETE /api/v1/repositories/{id}`
Disconnect repository and remove its tracking.
- **Response `200 OK`:** `{"status": "deleted", "id": "repo_111"}`

---

### 2.4 Pull Requests

#### `GET /api/v1/repositories/{id}/pull-requests`
List tracked pull requests for a repository.
- **Query Params:** `state` (`open`, `closed`, `all`; default: `open`)
- **Response `200 OK`:**
```json
[
  {
    "id": "pr_222",
    "pr_number": 42,
    "title": "feat: modernize client timeout parameter and update configuration",
    "state": "open",
    "author_username": "octocat",
    "base_ref": "main",
    "base_sha": "7f20563",
    "head_ref": "feat/modern-client",
    "head_sha": "cb6234f",
    "html_url": "https://github.com/Atharv386/DocSentary/pull/42",
    "latest_analysis": {
      "id": "run_333",
      "status": "completed",
      "drift_count": 1,
      "potential_drift_count": 0,
      "duration_ms": 380,
      "completed_at": "2026-11-01T03:32:00Z"
    },
    "created_at": "2026-11-01T03:00:00Z"
  }
]
```

#### `GET /api/v1/pull-requests/{id}`
Retrieve individual PR details, including changed files and full finding history.

#### `POST /api/v1/pull-requests/{id}/analyze`
Trigger an on-demand documentation drift analysis for this pull request.
- **Request Body (optional):**
```json
{
  "no_model": false,
  "force_rescan": true
}
```
- **Response `202 Accepted`:**
```json
{
  "analysis_run_id": "run_444",
  "status": "queued",
  "message": "Analysis queued for PR #42 at commit cb6234f"
}
```

---

### 2.5 Analyses & Runs

#### `GET /api/v1/analyses/{id}`
Retrieve status and results of an analysis run.
- **Response `200 OK`:**
```json
{
  "id": "run_333",
  "status": "completed",
  "trigger_type": "webhook_pr_sync",
  "base_sha": "7f20563",
  "head_sha": "cb6234f",
  "merge_base_sha": "7f20563",
  "tool_version": "0.2.0",
  "model_id": "qwen3:8b",
  "duration_ms": 380,
  "summary": {
    "changed_files": 2,
    "findings": 1,
    "drift": 1,
    "potential_drift": 0,
    "uncertain": 0,
    "code_facts": 4,
    "doc_spans": 6
  },
  "error_message": null,
  "created_at": "2026-11-01T03:31:58Z",
  "completed_at": "2026-11-01T03:32:00Z"
}
```

#### `GET /api/v1/analyses/{id}/findings`
Retrieve all findings and evidence generated by an analysis run.
- **Response `200 OK`:** Array of `Finding` objects detailed below.

---

### 2.6 Findings & Evidence Inspector

#### `GET /api/v1/findings/{id}`
Retrieve a single finding with all associated code and documentation evidence anchors.
- **Response `200 OK`:**
```json
{
  "id": "f_555",
  "finding_external_id": "DCS-DEFAULT-001",
  "status": "DRIFT",
  "resolution_status": "open",
  "resolution_reason": null,
  "severity": "high",
  "rule_id": "RULE_PARAM_DEFAULT_CHANGED",
  "category": "signature_drift",
  "title": "Default value for 'timeout' changed from 30 to 60",
  "explanation": "Function 'Client.__init__' updated parameter 'timeout' default to 60, but README.md states default is 30.",
  "confidence": 1.0,
  "verification": "deterministic",
  "suggested_action": "Update README.md at line 42 to document the new default timeout of 60.",
  "evidence": [
    {
      "id": "ev_doc_1",
      "evidence_external_id": "EV-DOC-42",
      "role": "documentation",
      "path": "README.md",
      "line_start": 42,
      "line_end": 44,
      "quote": "The client constructor takes `timeout` which defaults to 30 seconds.",
      "source_kind": "doc_span",
      "metadata": {"claim_type": "parameter_default"}
    },
    {
      "id": "ev_code_1",
      "evidence_external_id": "EV-CODE-10",
      "role": "code",
      "path": "src/client.py",
      "line_start": 10,
      "line_end": 14,
      "quote": "def __init__(self, timeout: int = 60):",
      "source_kind": "ast_fact",
      "metadata": {
        "symbol": "Client.__init__",
        "parameter": "timeout",
        "old_value": "30",
        "new_value": "60"
      }
    }
  ]
}
```

#### `PATCH /api/v1/findings/{id}/status`
Update finding resolution status.
- **Request Body:**
```json
{
  "resolution_status": "acknowledged",
  "resolution_reason": "Documentation will be updated in follow-up PR #43."
}
```
- **Response `200 OK`:** Updated finding object.

---

### 2.7 Webhooks & Health

#### `POST /api/v1/webhooks/github`
Inbound GitHub App webhook receiver.
- **Headers:**
  - `X-GitHub-Delivery`: Unique GUID.
  - `X-GitHub-Event`: Event name (`pull_request`, `ping`, etc.).
  - `X-Hub-Signature-256`: `sha256=<hmac_hex>`.
- **Response `202 Accepted`:** `{"status": "accepted", "event_id": "guid"}`
- **Response `401 Unauthorized`:** Invalid HMAC signature.
- **Response `409 Conflict`:** Webhook delivery already processed.

#### `GET /api/v1/health`
System health check.
- **Response `200 OK`:**
```json
{
  "status": "healthy",
  "version": "0.2.0",
  "database": "connected",
  "worker_queue": "idle"
}
```
