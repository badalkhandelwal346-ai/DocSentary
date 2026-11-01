# DocSentry — Authentication & User Onboarding Specification
**Version:** 1.0.0-auth  
**Scope:** Direct Sign-in, Email Signup, GitHub OAuth, and User Onboarding

---

## 1. Authentication Modalities

DocSentry provides dual authentication mechanisms:
1. **GitHub OAuth / GitHub App:** The primary developer identity path. Users authorize DocSentry, receiving access to their repositories and pull requests.
2. **Email & Password Authentication:** Supports independent developer registrations with `bcrypt` (work factor 12) password hashing and JWT session tokens.
3. **Developer Profile Switching:** For local testing and air-gapped development, direct token creation permits instant switching between workspace identities.

---

## 2. Onboarding Lifecycle (7-Step Wizard)

New users are guided through an onboarding wizard persisted in the database:

- **Step 1: Welcome & Value Proposition:** Introduction to AST-level documentation drift detection.
- **Step 2: Connect GitHub Account:** Authorizing GitHub OAuth or personal token permissions.
- **Step 3: GitHub App Installation:** Installing the DocSentry App on organizations or personal accounts.
- **Step 4: Repository Selection:** Discovering and selecting repositories for active drift monitoring.
- **Step 5: Analysis Preferences:** Configuring target documentation paths (`docs/**/*.md`) and model settings (deterministic vs. selective Qwen3-8B verifier).
- **Step 6: First Drift Scan:** Triggering the inaugural AST analysis on the default branch or open PR.
- **Step 7: Verification & Dashboard Launch:** Presenting initial drift findings and evidence anchors.

Users who have not completed onboarding are automatically routed to `/onboarding`.
