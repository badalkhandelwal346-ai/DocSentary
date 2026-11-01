# DocSentry — Current Product & Repository Audit
**Version:** 1.0.0-audit  
**Date:** 2026-11-01  
**Scope:** Complete component-by-component inventory of functional, partial, mock, and missing infrastructure.

---

## 1. Executive Summary

DocSentry began as a CLI drift detection prototype and a frontend demonstration dashboard. While the core Python detection engine (`Track A`) has achieved a stable detection baseline (`cb6234f`), the product application layer previously relied on hardcoded scenarios, fabricated commit hashes, and disconnected UI prototypes.

This audit provides a ruthless, honest assessment of what works, what is partially implemented, what relies on mock data, and what is missing to take DocSentry to a production SaaS.

---

## 2. Component Inventory Matrix

| Subsystem | Component | Status | Details / Issues | Remediation Required |
|---|---|---|---|---|
| **Core Intelligence** | `src/docsentry/pipeline.py` | **Fully Functional** | Static AST comparison, markdown span parser, deterministic rule engine. | Keep frozen; wrap in Engine Adapter. |
| **Core Intelligence** | `src/docsentry/cli.py` | **Fully Functional** | CLI commands (`scan`, `version`, `validate-report`). | Preserve 100% backward compatibility. |
| **Core Intelligence** | `src/docsentry/ai/verifier.py` | **Fully Functional** | Selective Qwen3-8B verifier via Ollama. | Abstract for configurable local/cloud inference. |
| **Backend API** | `backend/app/main.py` | **Functional Foundation** | FastAPI app with `/api/v1` routes and CORS. | Extend with user onboarding, evaluations, and real GitHub routes. |
| **Backend API** | `backend/app/core/security.py` | **Partially Implemented** | JWT encoding/decoding and HMAC verification. Missing bcrypt password hashing. | Implement bcrypt password hashing for direct signups. |
| **Backend API** | `backend/app/adapters/engine_adapter.py` | **Functional** | Bridges FastAPI to `scan_repository` with timeout protection. | Add sandboxed Git clone/fetch worker for remote GitHub repos. |
| **Database** | `backend/app/db/models/` | **Partially Implemented** | 11 models (User, Org, Repo, PR, AnalysisRun, Finding, Evidence, etc.). | Add `EvaluationRun` model and user `onboarding_completed` flag. |
| **Database** | `alembic/` | **Functional** | Alembic migrations running on SQLite & PostgreSQL. | Run migration for new fields. |
| **GitHub Integration**| `backend/app/services/github_service.py` | **Partially Implemented** | Webhook HMAC verification and deduplication. | Add live GitHub API client: list user repos, list PRs, read commit trees. |
| **Authentication** | Direct login & OAuth | **Partially Implemented** | Direct login and GitHub OAuth skeleton. Missing dedicated Signup page and password validation. | Implement dedicated Signup & Login pages, email registration, and session storage. |
| **Background Processing** | `analysis_worker.py` | **Placeholder / In-process** | Uses basic FastAPI background tasks. Missing detailed lifecycle stages. | Implement explicit state transitions: `QUEUED` → `CLONING` → `ANALYZING` → `VALIDATING` → `COMPLETED`. |
| **Frontend Styling** | `web/tailwind.config.js` | **Non-Conforming** | Uses generic dark theme (`brand-dark`, `brand-surface`). | **Replace with Tactile Pastoral & Analog Editorial design system.** |
| **Landing Page** | `web/src/components/LandingPage.tsx` | **Prototype / Generic** | Generic dark SaaS marketing page. Lacks the editorial/pastoral aesthetic. | Rewrite completely according to `DESIGN.md` and Parts 2 & 10. |
| **Dashboard** | `web/src/components/DashboardView.tsx` | **Partially Connected** | Fetches repos from API, but has mixed mock styling. | Redesign with warm paper aesthetic, real empty states, zero fake data. |
| **PR Analysis View** | `web/src/components/PRAnalysisView.tsx` | **Mock-Dependent** | Imports and defaults to `mockScenarios.ts`. | **Completely detach mock data.** Connect to real GitHub PR API. |
| **Evidence Inspector** | `web/src/components/EvidenceComparison.tsx` | **Functional Core, Dark Style** | Has side-by-side diffing and resolution buttons. | Style with dark cyanotype surfaces, high-contrast monospace AST facts. |
| **Evaluations** | `web/src/components/BenchmarkView.tsx` | **Hardcoded Prototype** | Renders static benchmark tables. | Connect to backend `/evaluations` endpoint and persisted evaluation reports. |
| **Onboarding** | Onboarding Flow | **Missing Entirely** | No step-by-step onboarding wizard. | Build real 7-step onboarding wizard with persistent completion status. |
| **Deployment** | `render.yaml` & Dockerfiles | **Missing / Incomplete** | Has local Dockerfile and Docker Compose. Missing Render Blueprint. | Create `render.yaml` and production deployment pipeline. |

---

## 3. Fabricated / Fake Data Elimination Plan

The following files contain hardcoded mock data that will be removed from all production paths:
1. `web/src/data/mockScenarios.ts`: Contains fabricated scenarios (`scenario-1`, `scenario-2`, `scenario-3`, `scenario-4`).
2. Hardcoded fallback statistics in dashboard cards.
3. Invented repository lists and commit histories.

### Replacement Strategy:
- When a user signs in, their actual accessible GitHub repositories are retrieved via the GitHub API (`https://api.github.com/user/repos`).
- When a repository is selected, its real pull requests are retrieved (`https://api.github.com/repos/{owner}/{repo}/pulls`).
- When an analysis is triggered, the engine adapter clones/fetches the real git revisions and executes AST comparison.
- When no data exists, the application displays clean, editorial empty states guiding the user to connect their first repository.

---

## 4. Production Readiness Roadmap

1. **Phase 1: Design System & Styling:** Install Google fonts (`Newsreader`, `Instrument Serif`, `Geist`, `JetBrains Mono`), configure Tailwind tokens (`#F4EFE6`, `#1C354D`, `#4A6B32`, `#C87D55`), and build reusable editorial components.
2. **Phase 2: Public Website:** Build the editorial landing page with the pastoral aesthetic, problem illustration, workflow diagram, and real CTAs.
3. **Phase 3: Auth & Onboarding:** Dedicated Signup, Login, and 7-step Onboarding flow with backend user persistence.
4. **Phase 4: Real GitHub Integration:** Live OAuth token exchange, repository discovery, PR fetching, and webhook handling.
5. **Phase 5: Remote Repo Cloning & Engine Execution:** Background worker cloning pull request revisions in a sandboxed cache and running `docsentry.pipeline`.
6. **Phase 6: Rebuilt Authenticated App:** Dashboard, Repositories, PR Analysis, Evidence Inspector, Evaluations, and Settings, all backed by real PostgreSQL data.
7. **Phase 7: Production Deployment:** Render Blueprint (`render.yaml`), Dockerfiles, and deployment verification.
