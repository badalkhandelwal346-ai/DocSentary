# DocSentry — Production Infrastructure & Hacktoberfest Benefits Inventory
**Version:** 1.0.0-infra  
**Context:** Hack Day Sonipat / Hacktoberfest 2026 Developer Tooling & Cloud Benefits

---

## 1. Hacktoberfest & Developer Benefits Inventory

| Provider | Capability Provided | Benefit / Free Tier Terms | Payment Method Required | Suitability for DocSentry | Production Decision |
|---|---|---|---|---|---|
| **Render** | Full Stack Cloud (Web Services, Static Sites, PostgreSQL, Background Workers) | Free Tier + Hackathon credits ($5/mo static, free tier web services with 512MB RAM, managed PostgreSQL with 1GB storage, native background workers). | Optional on free tier; required for paid instances | **High:** Unified platform supporting Python FastAPI, React Static Sites, PostgreSQL, and background worker threads under one single `render.yaml` Blueprint. | **Primary Production Target** |
| **GitHub Actions** | CI/CD & Automated PR Workflows | 2,000 free runner minutes/month for public/private repositories. | No | **High:** Native GitHub integration for automated test runs, Docker builds, and DocSentry PR evaluation benchmarks. | **Primary CI/CD Provider** |
| **GitHub Apps / Marketplace** | Developer Identity & Webhooks | Free listing and free webhook deliveries (no volume caps). | No | **Essential:** Official mechanism for receiving pull request events, authenticating users, and posting Check Runs. | **Primary Integration Gateway** |
| **PostgreSQL (Render Managed)** | Relational Persistence | Managed PostgreSQL 15/16, SSL encrypted, automatic connection pooling. | Free tier: 1GB limit, 30 days inactivity limit on free instances. Paid starting at $7/mo. | **High:** Zero-ops managed database perfectly matching SQLAlchemy 2.0 and Alembic. | **Selected Database** |
| **Upstash / Redis** | Distributed Job Queue & Rate Limiting | 10,000 commands/day free serverless Redis. | No | **Medium:** Excellent for high-volume Celery/RQ task queues. For DocSentry v0.2.0, FastAPI in-process worker / PostgreSQL task locking satisfies scale with lower architectural complexity. | **Future Scale (v0.3+)** |
| **Cloudflare** | DNS, CDN, SSL & Edge Protection | Free universal SSL, unlimited bandwidth, edge caching, DDoS mitigation. | No | **High:** Fronts custom domain (`docsentry.dev` or subdomains) with zero egress fees. | **Selected DNS / CDN Layer** |
| **Ollama / Local Inference** | Open-Weight Model (Qwen3-8B) | 100% free local execution on Apple Silicon (M4, 16GB unified memory). Zero cloud cost, zero privacy leakage. | No | **Essential for Dev:** Primary verifier for local testing. In production cloud, engine defaults to deterministic AST rules with optional self-hosted endpoint. | **Dual Strategy: Deterministic Cloud + Local LLM Dev** |

---

## 2. Infrastructure Selection Rationales

### Why Render as Primary PaaS?
1. **Unified Infrastructure as Code:** A single [`render.yaml`](file:///Users/atharvupadhyay/Documents/Coding%20Projects/HACKTOBER%20FEST%202K26/DocSentary/render.yaml) defines the React static frontend, the FastAPI web service, the PostgreSQL relational store, and the background worker.
2. **Native Git Integration:** Direct deployment on commit push to GitHub branches without requiring complex external deployment orchestrators.
3. **Environment Security:** Secrets (`DOCSENTRY_SECRET_KEY`, `DOCSENTRY_GITHUB_CLIENT_SECRET`, `DOCSENTRY_GITHUB_WEBHOOK_SECRET`) are managed securely in Render's dashboard and injected as environment variables.
4. **Predictable Pricing Post-Credits:** Generous free tier for hackathon launch, scaling transparently to $7/mo for persistent databases when scaling.
