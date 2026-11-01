# DocSentry — Production Setup & Cloud Configuration
**Version:** 1.0.0-prodsetup  
**Hosting Providers:** Render / Self-Hosted Docker / PostgreSQL Managed

---

## 1. Environment Variable Reference

| Variable | Environment | Description |
|---|---|---|
| `DOCSENTRY_ENV` | Production | Set to `production`. |
| `DOCSENTRY_DATABASE_URL` | Production | Managed PostgreSQL connection string (`postgresql+psycopg://...`). |
| `DOCSENTRY_SECRET_KEY` | Production | High-entropy 64-character random key for signing JWTs. |
| `DOCSENTRY_GITHUB_CLIENT_ID` | Production | GitHub App Client ID from developer settings. |
| `DOCSENTRY_GITHUB_CLIENT_SECRET` | Production | GitHub App Client Secret. |
| `DOCSENTRY_GITHUB_WEBHOOK_SECRET`| Production | Secret used to verify HMAC SHA-256 signatures on inbound PR webhooks. |
| `VITE_API_BASE_URL` | Production (Frontend) | URL of the public FastAPI backend (e.g. `https://api.docsentry.dev/api/v1`). |

---

## 2. GitHub App Production Setup

1. In GitHub, navigate to **Settings** → **Developer settings** → **GitHub Apps** → **New GitHub App**.
2. **App Name:** `DocSentry Documentation Intelligence`
3. **Homepage URL:** `https://docsentry.onrender.com`
4. **Webhook URL:** `https://docsentry-api.onrender.com/api/v1/webhooks/github`
5. **Webhook Secret:** Set a secure random string and paste into `DOCSENTRY_GITHUB_WEBHOOK_SECRET`.
6. **Permissions:**
   - *Pull requests:* Read & write
   - *Contents:* Read-only
   - *Checks:* Read & write
   - *Metadata:* Read-only
7. **Subscribe to events:** `pull_request`, `installation`, `ping`.
