# DocSentry — Deployment & Infrastructure Architecture
**Version:** 0.2.0-deploy  
**Target Environments:** Local Development, Docker Compose, Production Kubernetes / Cloud Run

---

## 1. Container Architecture

DocSentry is packaged into two lean, production-grade container images:
1. `docsentry-backend`: FastAPI API server and background worker runner (Python 3.11/3.12/3.14).
2. `docsentry-web`: High-performance Nginx static web server serving the compiled React/Vite bundle.

```
+-----------------------------------------------------------------------------+
|                           DOCKER COMPOSE TOPOLOGY                           |
|                                                                             |
|   +-----------------------+              +------------------------------+   |
|   | Nginx Frontend        |   Reverse    | FastAPI Backend API          |   |
|   | (Port 80 / 5173)      |  --------->  | (Port 8000)                  |   |
|   | /web (Vite React app) |    Proxy     | Uvicorn Async Server         |   |
|   +-----------------------+              +------------------------------+   |
|                                                         |                   |
|                                      +------------------+                   |
|                                      |                                      |
|                                      v                                      |
|                       +------------------------------+                      |
|                       | PostgreSQL Database          |                      |
|                       | (Port 5432)                  |                      |
|                       | Relational Data & Migrations |                      |
|                       +------------------------------+                      |
+-----------------------------------------------------------------------------+
```

---

## 2. Docker Compose Specification (`docker-compose.yml`)

```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    container_name: docsentry-db
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-docsentry}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-docsentry_secret}
      POSTGRES_DB: ${POSTGRES_DB:-docsentry_prod}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U docsentry -d docsentry_prod"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: docsentry-backend
    restart: always
    depends_on:
      db:
        condition: service_healthy
    environment:
      - DOCSENTRY_ENV=production
      - DOCSENTRY_DATABASE_URL=postgresql+psycopg://docsentry:docsentry_secret@db:5432/docsentry_prod
      - DOCSENTRY_SECRET_KEY=${DOCSENTRY_SECRET_KEY}
      - DOCSENTRY_GITHUB_CLIENT_ID=${DOCSENTRY_GITHUB_CLIENT_ID}
      - DOCSENTRY_GITHUB_CLIENT_SECRET=${DOCSENTRY_GITHUB_CLIENT_SECRET}
      - DOCSENTRY_GITHUB_WEBHOOK_SECRET=${DOCSENTRY_GITHUB_WEBHOOK_SECRET}
    ports:
      - "8000:8000"

  web:
    build:
      context: ./web
      dockerfile: Dockerfile
    container_name: docsentry-web
    restart: always
    depends_on:
      - backend
    ports:
      - "3000:80"

volumes:
  postgres_data:
```

---

## 3. Environment Variable Reference

| Variable Name | Required | Default (Dev) | Description |
|---|---|---|---|
| `DOCSENTRY_ENV` | Yes | `development` | Environment mode (`development`, `test`, `production`). |
| `DOCSENTRY_DATABASE_URL` | Yes | `sqlite:///./docsentry.db` | SQLAlchemy database connection string. |
| `DOCSENTRY_SECRET_KEY` | Yes | (auto-generated in dev) | Cryptographic secret for signing JWT auth tokens. |
| `DOCSENTRY_GITHUB_CLIENT_ID` | Conditional | `None` | GitHub OAuth / App Client ID. |
| `DOCSENTRY_GITHUB_CLIENT_SECRET` | Conditional | `None` | GitHub OAuth / App Client Secret. |
| `DOCSENTRY_GITHUB_WEBHOOK_SECRET`| Conditional | `None` | Secret used to verify `X-Hub-Signature-256`. |
| `DOCSENTRY_GITHUB_APP_ID` | Conditional | `None` | GitHub App ID for check runs and bot tokens. |
| `DOCSENTRY_GITHUB_PRIVATE_KEY` | Conditional | `None` | PEM-formatted private key for GitHub App authentication. |
| `DOCSENTRY_CORS_ORIGINS` | No | `http://localhost:5173,http://localhost:3000` | Allowed CORS origins (comma-separated). |
| `DOCSENTRY_LOG_LEVEL` | No | `INFO` | Application log verbosity (`DEBUG`, `INFO`, `WARNING`). |

---

## 4. Local Development Quickstart

1. **Python Virtual Environment & Backend:**
   ```bash
   cd DocSentary
   source .venv/bin/activate
   pip install -e .
   pip install fastapi uvicorn sqlalchemy alembic pydantic-settings
   uvicorn backend.app.main:app --reload --port 8000
   ```

2. **Frontend Development Server:**
   ```bash
   cd DocSentary/web
   npm install
   npm run dev
   ```

3. **Running Migrations:**
   ```bash
   cd DocSentary/backend
   alembic upgrade head
   ```

4. **Running Tests:**
   ```bash
   # Core detection tests
   pytest tests/unit/
   # Backend API & Multi-Tenancy tests
   pytest backend/tests/
   ```
