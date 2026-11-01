# DocSentry — Product Roadmap & Milestones
**Version:** 0.2.0-roadmap  
**Horizon:** v0.2.0 through v1.0.0

---

## 1. Development Phases & Current Status

```
[==================== PHASE A: AUDIT & ARCHITECTURE (COMPLETED) ====================]
  ✓ Repository & CLI audit
  ✓ Database schema design
  ✓ REST API specification
  ✓ GitHub integration architecture
  ✓ Security & multi-tenancy model
  ✓ Engine adapter pattern

[==================== PHASE B: BACKEND FOUNDATION (IN PROGRESS) ====================]
  → FastAPI application structure
  → SQLAlchemy 2.0 models & Alembic migrations
  → JWT Authentication & multi-tenancy dependency guards
  → Health & system metrics API

[==================== PHASE C: ENGINE ADAPTER & PERSISTENCE ========================]
  → Robust DocSentryEngineAdapter
  → AnalysisRun, Finding, and Evidence persistence
  → Verification tests matching CLI output

[==================== PHASE D: FRONTEND EXPERIENCE & EVIDENCE INSPECTOR ============]
  → Polished Landing / Marketing page
  → Central API client & Auth state
  → Real Multi-tenant Dashboard
  → Repository detail & PR analysis screens
  → Rich Evidence Inspector (Code vs Doc, AST facts, Provenance)

[==================== PHASE E: ASYNC PROCESSING & QUEUES ===========================]
  → Background job worker
  → Task deduplication
  → State transitions (queued -> processing -> completed / failed)

[==================== PHASE F: GITHUB APP INTEGRATION ==============================]
  → Webhook signature verification (HMAC SHA-256)
  → Delivery ID deduplication
  → Check Runs status reporting & dashboard deep links

[==================== PHASE G: PRODUCTION READINESS & VERIFICATION =================]
  → Multi-tenancy cross-access test suite
  → Docker Compose environment
  → Complete documentation and .env.example
```

---

## 2. Release Milestones

### Milestone 1: v0.2.0 — First Full-Stack Release (Current Objective)
- Working FastAPI backend connected to SQLite / PostgreSQL.
- Engine adapter executing non-invasive scans against git snapshots.
- Real-time PR Analysis and Evidence Inspector in React frontend.
- Mock / Honest GitHub setup state for environments without live GitHub credentials.
- Multi-tenancy security tests preventing cross-tenant leakage.

### Milestone 2: v0.3.0 — Continuous GitHub PR Checks
- Official GitHub Marketplace App listing.
- Automated Check Run annotations inline on modified markdown files.
- Automated PR comment summaries with drill-down links.
- Team Slack / Discord notifications for new documentation drifts.

### Milestone 3: v0.4.0 — One-Click Documentation Auto-Remediation
- "Suggest Doc Fix" button in Evidence Inspector: generates exact Markdown patch resolving the drift.
- GitHub bot commits suggested fix directly to the pull request branch upon approval.

### Milestone 4: v1.0.0 — Enterprise Multi-Language & Monorepos
- Monorepo package-boundary awareness (independent `docsentry.yml` per subproject).
- Multi-language AST support (TypeScript / JavaScript, Go, Rust in addition to Python).
- SOC2 compliance, audit logs export, and SSO (SAML/Okta) integration.
