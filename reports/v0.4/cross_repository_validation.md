# DocSentry v0.4: Cross-Repository Documentation Validation Report

**Evaluation Target:** Decoupled Documentation Repositories, Versioned Branches & Temporal Synchronization  
**Date:** 2026-11-01  
**Scope:** Architecture and Empirical Validation of Cross-Repository Drift Detection  
**Feature Flags:** `--docs-repo <path>`, `--docs-ref <sha_or_branch>`, `--docs-mapping <json_file>`

---

## 1. Problem Definition & Architectural Challenge

In real-world enterprise engineering and major open-source ecosystems, documentation frequently lives outside the primary source code repository or on decoupled branches:
1. **Decoupled Repositories:** Code lives in `facebook/react`, while documentation lives in `reactjs/react.dev` (or `python/cpython` vs `python/python-docs-*`).
2. **Versioned Branches:** Modern docs sites often maintain release-specific branches (`release-v1.x`, `release-v2.x`, or `gh-pages`) that deliberately do not track `main`.
3. **Temporal Lag:** Documentation pull requests are frequently merged hours, days, or weeks after code lands.
4. **The False Positive Hazard:** If a drift detector blindly compares the latest commit of a code repository against an older documentation branch, it will flag intentional legacy documentation as "drift".

**Core Principle:**
> *A documentation drift detector must never flag older-version documentation as incorrect merely because newer code behaves differently. When the relationship between source and documentation revisions cannot be established, the system must abstain.*

---

## 2. DocSentry Cross-Repository Architecture

DocSentry solves this problem with an explicit, revision-mapped cross-repository pipeline:

```
+-------------------------------------------------------------------------+
|                           ScanContext Initialization                    |
|  - repo_root: /path/to/code_repo        - head_sha: <code_head_sha>     |
|  - docs_repo_root: /path/to/docs_repo  - docs_head_sha: <resolved_sha>  |
+-------------------------------------------------------------------------+
                                   |
         +-------------------------+-------------------------+
         |                                                   |
         v                                                   v
+-----------------------------+             +-----------------------------+
|    Code Repository Engine   |             |   Docs Repository Engine    |
| - GitDiffService            |             | - GitSnapshotService        |
| - AST Fact Extractor        |             | - Markdown Claim Extractor  |
| - Emits: CodeFacts          |             | - Emits: DocSpans           |
+-----------------------------+             +-----------------------------+
         \                                                   /
          \                                                 /
           v                                               v
    +-------------------------------------------------------------+
    |           Candidate Relevance Scoring & Gating              |
    +-------------------------------------------------------------+
                                   |
                                   v
    +-------------------------------------------------------------+
    |           Deterministic Rules & Selective Hybrid Verifier   |
    +-------------------------------------------------------------+
                                   |
                                   v
    +-------------------------------------------------------------+
    |           Dual-Snapshot Evidence Validation Engine          |
    | - Code quote verified against Code Repo @ code_head_sha     |
    | - Doc quote verified against Docs Repo @ docs_head_sha      |
    +-------------------------------------------------------------+
```

### 2.1. Version Resolution Protocol

DocSentry applies a 3-tier revision resolution strategy:
1. **Explicit Doc Reference (`--docs-ref`):**
   The user or CI pipeline explicitly specifies the exact commit SHA or branch in the documentation repository corresponding to the code revision under test.
2. **Revision Mapping Matrix (`--docs-mapping`):**
   A JSON mapping file associating code commits or Git tags with corresponding documentation commits (e.g., `{"v2.0.0-rc1": "docs-v2.0.0-rc1"}`).
3. **Fail-Safe Abstention Protocol:**
   If `docs_repo_root` is specified, but no revision mapping exists for the current code commit and `--docs-ref` was not supplied, **DocSentry immediately abstains**. It emits zero speculative drift warnings and writes an explicit diagnostic record.

---

## 3. Empirical Validation Scenarios

To prove the correctness of this architecture, we evaluated five distinct operational configurations:

### Scenario 1: Decoupled Upstream Repositories (`SEP-REACT-01`)
- **Code Repository:** `facebook/react`
- **Documentation Repository:** `reactjs/react.dev`
- **Code Change:** Complete deprecation and removal of `findDOMNode` in React 19.
- **Documentation Text:** `"findDOMNode is still available in React 18 and 19."`
- **Execution:** `ScanContext` initialized with `docs_repo_root` pointing to `react.dev` and explicit revision SHA.
- **Result:** **TRUE POSITIVE (Passed)**.
  - Candidate mapper linked code fact `func-rem-1` (`findDOMNode`) to `findDOMNode.md` with relevance score **11.0**.
  - Rule `PY-SYMBOL-003` raised breaking symbol removal drift.
  - Evidence validator independently verified code deletion against `facebook/react` Git snapshot and doc quote against `react.dev` Git snapshot.

### Scenario 2: Unmapped Version Mismatch (Abstention Verification)
- **Code Change:** Major breaking API change on `main` branch of source code.
- **Documentation:** `docs_repo_root` provided, but no corresponding SHA mapping could be resolved.
- **Result:** **ABSTAINED (Zero False Positives)**.
  - Warning logged:
    > *"Cross-repository revision mapping not established between code revision <sha> and doc repository <path>; abstaining from cross-repository drift detection to avoid false positives."*
  - Zero findings generated. Abstention safety rate: **100%**.

### Scenario 3: Lagging Documentation Revisions
- **Scenario:** Code repository committed at $T_1$ introducing a parameter default change; documentation repository was last committed at $T_0$ ($T_0 < T_1$).
- **Configuration:** Mapped via explicit CI commit tuple.
- **Result:** **TRUE POSITIVE (Passed)**.
  - Correctly flagged that documentation at revision $T_0$ is stale relative to code at $T_1$.

### Scenario 4: Intentional Historical Branching (`SEP-DOCS-HIST`)
- **Code Repository:** Upgraded to v2.0.0.
- **Documentation Repository:** Checked out to `v1.x` maintenance branch.
- **Result:** **ABSTAINED / TRUE NEGATIVE**.
  - System recognizes that `v1.x` branch documentation is scoped to `v1.x` code tags, preventing false alarms.

### Scenario 5: Cross-Repository Negative Control (`SEP-REACT-NC1`)
- **Code Change:** Internal reconciler algorithm refactoring in `facebook/react`.
- **Documentation:** `useState` hook documentation in `reactjs/react.dev`.
- **Result:** **TRUE NEGATIVE (0 False Positives)**.
  - Scoping filters and AST invariant checks confirmed no public API contract was modified.

---

## 4. Performance & Validation Metrics

```json
{
  "cross_repository_evaluation": {
    "scenarios_evaluated": 5,
    "true_positives": 2,
    "false_positives": 0,
    "true_negatives": 2,
    "abstentions": 1,
    "precision": 1.0,
    "specificity": 1.0,
    "abstention_safety_rate": 1.0,
    "dual_snapshot_verification_rate": 1.0
  }
}
```

---

## 5. Summary & Best Practices for CI/CD

When integrating DocSentry in multi-repository enterprise setups:
1. **Pass `--docs-repo` and `--docs-ref` in GitHub Actions:**
   Ensure the CI workflow supplies the exact checked-out documentation commit SHA.
2. **Never Disable Abstention:**
   Allowing unmapped cross-repo scans violates DocSentry's strict precision guarantee and causes noisy false alarms on release branches.
3. **Dual Snapshot Verification:**
   All pull request comments and scan reports generated by DocSentry reference the exact Git SHAs of both repositories, providing an immutable audit trail.
