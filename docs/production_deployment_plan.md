# DocSentry — Production Deployment Plan & Blueprint
**Version:** 1.0.0-deployplan  
**Target Platform:** Render Cloud + Managed PostgreSQL + Cloudflare DNS

---

## 1. Production Topology & Architecture

```
[ Developer / Browser ]
           |
           v HTTPS (Custom Domain: app.docsentry.dev / docsentry.onrender.com)
+------------------------------------------------------------------------------------+
|                               CLOUDFLARE EDGE / CDN                                |
|                        (DDoS Protection, SSL Termination)                         |
+------------------------------------------------------------------------------------+
           |                                                      |
           v Static Assets (React 18 / Vite)                      v REST API Requests
+------------------------------------+      +----------------------------------------+
|        RENDER STATIC SITE          |      |          RENDER WEB SERVICE            |
|       `docsentry-frontend`         |      |           `docsentry-api`              |
|                                    |      |       FastAPI / Python 3.12            |
| - Tactile Pastoral Design System   |      | - Multi-tenant Authentication          |
| - React 18 / TypeScript / Vite     |      | - Real GitHub OAuth & Repo Discovery   |
| - Central Typed API Client         |      | - Background Job Worker                |
+------------------------------------+      +----------------------------------------+
                                                               |
                                   +---------------------------+---------------------+
                                   |                                                 |
                                   v                                                 v
                  +--------------------------------+               +----------------------------------+
                  |       RENDER POSTGRESQL        |               |       SANDBOXED GIT CACHE        |
                  |          `docsentry-db`        |               |      (Transient Ephemeral Disk)  |
                  |                                |               |                                  |
                  | - Multi-tenant isolation       |               | - Clones base & head revisions   |
                  | - Persisted AnalysisRuns       |               | - Executes static AST extraction |
                  | - Findings & Evidence anchors  |               | - Zero code execution            |
                  | - Webhook delivery audit trail |               +----------------------------------+
                  +--------------------------------+
```

---

## 2. Infrastructure as Code (`render.yaml`)

```yaml
services:
  # 1. Backend FastAPI Service
  - type: web
    name: docsentry-api
    runtime: python
    buildCommand: "pip install --upgrade pip && pip install -e . && pip install fastapi uvicorn sqlalchemy alembic pydantic-settings pyjwt cryptography psycopg[binary] bcrypt httpx && alembic upgrade head"
    startCommand: "uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DOCSENTRY_ENV
        value: production
      - key: DOCSENTRY_DATABASE_URL
        fromDatabase:
          name: docsentry-db
          property: connectionString
      - key: DOCSENTRY_SECRET_KEY
        generateValue: true
      - key: DOCSENTRY_GITHUB_CLIENT_ID
        sync: false
      - key: DOCSENTRY_GITHUB_CLIENT_SECRET
        sync: false
      - key: DOCSENTRY_GITHUB_WEBHOOK_SECRET
        sync: false

  # 2. Frontend React / Vite Static Site
  - type: static_site
    name: docsentry-web
    buildCommand: "cd web && npm ci && npm run build"
    staticPublishPath: "./web/dist"
    routes:
      - type: rewrite
        source: "/*"
        destination: "/index.html"
    envVars:
      - key: VITE_API_BASE_URL
        fromService:
          type: web
          name: docsentry-api
          property: url

databases:
  # 3. Production Managed PostgreSQL Database
  - name: docsentry-db
    databaseName: docsentry_prod
    user: docsentry_user
    plan: starter
```

---

## 3. Deployment Execution Checklist

1. **Repository Push:** Ensure branch `feat/product-engineering` is pushed to GitHub (`Atharv386/DocSentary`).
2. **Connect to Render:**
   - Log into Render (`dashboard.render.com`).
   - Click **Blueprints** → **New Blueprint Instance**.
   - Select repository `Atharv386/DocSentary` and choose branch `feat/product-engineering`.
3. **Configure Secrets in Render Dashboard:**
   - `DOCSENTRY_GITHUB_CLIENT_ID`: From GitHub App Developer Settings.
   - `DOCSENTRY_GITHUB_CLIENT_SECRET`: Generated secret from GitHub App.
   - `DOCSENTRY_GITHUB_WEBHOOK_SECRET`: Pre-shared secret matching GitHub webhook setting.
4. **Automatic Provisioning:** Render creates the PostgreSQL database, applies Alembic migrations, starts the FastAPI service, and serves the static frontend.
