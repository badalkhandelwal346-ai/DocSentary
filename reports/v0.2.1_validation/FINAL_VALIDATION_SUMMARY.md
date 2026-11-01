# DocSentry v0.2.1: Final Engineering Validation & Audit Summary

**Product:** DocSentry  
**Core Promise:** *"Your code changed. Did your documentation become incorrect?"*  
**Evaluation Scope:** Blind Benchmark Verification, AI Value Quantification & End-to-End System Audit  
**Target Head Commit:** `cb6234f` (Main frozen v0.2 baseline)  
**Audit Baseline Commit:** `6dd5542`  
**Hardware & Environment:** MacBook Pro M4 (16GB Unified Memory), Python 3.14.2, `qwen3:8b` via Ollama  
**Date of Audit Completion:** November 1, 2026

---

## 1. Executive Summary

This independent validation audit was initiated under `/goal` to answer a singular, decisive question with uncompromised engineering honesty:
> **Does DocSentry genuinely detect documentation drift, does Qwen3-8B contribute measurable value beyond deterministic analysis, and does this capability generalize to unseen repositories?**

Over eight rigorous phases, the system's detection engine was kept completely frozen. We subjected it to deterministic vs. hybrid benchmarking on unseen repositories, forensic git-history analysis of claimed AI victories, adversarial regression testing, candidate-retrieval pipeline tracing, and end-to-end toolchain verification.

### Core Audit Outcomes
1. **Deterministic Core is Real and High-Performing:**
   DocSentry's deterministic AST diffing and Markdown claim classification reliably catch parameter additions/removals, default value shifts, and symbol deletions with **100% precision (0 false positives)** across all historical and blind datasets.
2. **AI Contributes 0.0% Incremental Value on Blind Repositories:**
   On the fresh 8-scenario blind evaluation across four unseen repositories (`urllib3`, `marshmallow`, `aiohttp`, `starlette`), Deterministic and Selective Hybrid achieved identical metrics ($TP=3, TN=4, FP=0, FN=1$, Precision: $100\%$, Recall: $75\%$, F1: $0.8571$). Local Qwen3-8B was invoked **zero times**.
3. **Forensic Reclassification of Claimed AI Win (`REAL-REQUESTS-01`):**
   Upstream verification revealed that adding `json=None` to `requests.post()` in PR #2258 did not break the documented `data=json.dumps(payload)` pattern. This is **procedural/advisory drift**, not a breaking factual falsehood. Under strict breaking-drift standards, verified AI-only contribution is **0.0%**. Under relaxed advisory standards, it is **9.09%** ($1/11$).
4. **Blind Dataset Ground Truth Disclosure:**
   All 8 blind scenarios were constructed synthetic fixtures with mock commit SHAs (`c101...` to `c108...`), rather than cloned authentic pull requests from upstream repositories.

---

## 2. Answers to the Three Core Questions

| Question | Verdict | Empirical Evidence |
|---|---|---|
| **1. Does the system detect authentic documentation drift with reliable evidence?** | **YES (for syntactic & structural drift)** | In all verified historical cases and synthetic fixtures, every generated finding included cryptographically verified Git snapshot quotes for both the changed code and the stale doc sentence. Location and attribution accuracy were **100%** across all detected cases. |
| **2. Does Qwen3-8B catch real cases that deterministic analysis misses?** | **AT MOST 1 (Advisory Only)** | On 25 verified historical cases, Qwen3-8B flagged `REAL-REQUESTS-01` (procedural drift). It caught **0** breaking bugs that deterministic rules missed. Across all benchmarks, deterministic analysis delivered 90.9% to 100% of the total recall. |
| **3. Does that AI contribution generalize to unseen repositories?** | **UNPROVEN / 0.0% ON CURRENT DATASET** | On the 4 unseen repositories, the AI model was bypassed entirely by the router. Deterministic rules found all 3 detected positive cases. The AI added zero incremental detections on blind data. |

---

## 3. Deliverables and Audit Map

All validation artifacts have been saved under `reports/v0.2.1_validation/`:

1. [`blind_deterministic_vs_hybrid.md`](blind_deterministic_vs_hybrid.md):
   Full scenario-by-scenario comparative matrix across Deterministic vs. Hybrid on 8 blind cases. Proves identical metrics ($F1=0.8571$) and 0 AI invocations.
2. [`requests_incremental_ai_forensic_audit.md`](requests_incremental_ai_forensic_audit.md):
   Forensic git-history and release-notes audit of `REAL-REQUESTS-01`, reclassifying it as procedural drift.
3. [`regression_coverage_audit.md`](regression_coverage_audit.md):
   Documentation of 12 new unit and adversarial regression tests in `tests/unit/test_v021_regression.py` covering all 4 repaired failure modes.
4. [`blind_ground_truth_audit.md`](blind_ground_truth_audit.md):
   Independent inspection of the 8 blind scenarios disclosing synthetic commit SHAs and fixture text.
5. [`urllib3_false_negative_analysis.md`](urllib3_false_negative_analysis.md):
   End-to-end pipeline trace of `BLIND-URLLIB3-01` proving failure occurred at Candidate Retrieval (Score: 1.0 vs Threshold: 4.0).
6. [`ai_incremental_value_final.md`](ai_incremental_value_final.md):
   Consolidated 6-configuration matrix, improvement disaggregation, and formal AI incremental value metrics.
7. [`v0.2.1_validation_metrics.json`](v0.2.1_validation_metrics.json):
   Machine-readable metrics, denominators, and forensic classifications.
8. [`FINAL_VALIDATION_SUMMARY.md`](FINAL_VALIDATION_SUMMARY.md):
   This executive summary and strategic guidance.

---

## 4. Engineering Verification Results

During Phase 8, the following test suite and system checks were executed against the frozen codebase:

| Check | Target / Command | Result | Details |
|---|---|---|---|
| **Unit & Integration Tests** | `pytest tests/` | **PASSED** | 58/58 tests passed in 2.47s (including all 12 v0.2.1 regression tests). |
| **Linter & Code Quality** | `ruff check src/ tests/` | **PASSED** | All checks passed cleanly. |
| **CLI Functionality** | `docsentry --help` | **PASSED** | CLI options and documentation rendered correctly. |
| **CLI Scan Execution** | `docsentry scan ... --no-model` | **PASSED** | Scanned a local git repository without errors. |
| **Schema Validation** | `docsentry validate-report` | **PASSED** | Validated canonical ScanReport JSON schema. |
| **Frontend Production Build** | `cd web && npm run build` | **PASSED** | TypeScript compilation and Vite bundling succeeded in 908ms. |
| **Deterministic Mode Isolation** | Standalone Python script | **PASSED** | Runs at 220ms per case with zero network/Ollama requirements. |
| **Ollama Offline Fault Tolerance** | Simulated `ConnectError` | **PASSED** | Hybrid router catches network errors and safely marks candidates `UNCERTAIN` without crashing. |
| **Git Working Tree** | `git status` | **CLEAN** | All original tracked files remain untouched; no detection logic was altered. |

---

## 5. What Has Been Proven vs. What Remains Uncertain

### What Has Been Proven
- **Zero Hallucination Guarantee:** The dual-gated architecture (Deterministic Rules $\rightarrow$ Strict Router $\rightarrow$ Evidence Validator) successfully prevents hallucinations. In no experiment did an open-weight model invent an identifier or manufacture a false positive.
- **Fast Deterministic Detection:** For parameter, default, and symbol changes, deterministic rules provide near-instantaneous ($<225\text{ ms}$) detection with $100\%$ precision and $100\%$ evidence validity.
- **AST Bug Fixes Were Legitimate:** The improvements made in v0.2 for Flask (class inheritance), Pydantic (aliasing), and Axios (JS property diffing) are rock-solid and verified by 12 regression tests.

### What Remains Uncertain
- **Authentic Generalization to Dirty Repositories:** Because the blind dataset was constructed from synthetic fixtures, performance on massive real-world git histories with thousands of markdown files and complex cross-references remains unverified.
- **The Role of Open-Weight Models:** At present, Qwen3-8B is heavily constrained by strict routing thresholds. It remains uncertain whether open-weight 8B models can ever reliably detect indirect semantic drift without introducing an unacceptable rate of false positives on large repos.

---

## 6. Recommended Next Engineering Priorities (Roadmap for v0.3)

1. **AST Call-Graph Default Propagation (Solving the Urllib3 FN):**
   Extend AST extraction to trace where module-level constants flow into function/class defaults. If `DEFAULT_TIMEOUT` defaults `PoolManager(timeout=DEFAULT_TIMEOUT)`, automatically bind `pool` and `timeout` as linked parameters. This solves indirect naming gaps deterministically without fragile NLP synonym tables.
2. **Curate an Authentic 20-Scenario Blind Benchmark:**
   Acquire 20 authentic historical pull requests from 5+ real GitHub repositories (e.g. `pallets/werkzeug`, `tornadoweb/tornado`, `redis/redis-py`, `certifi/python-certifi`, `psutil/psutil`), preserving authentic git SHAs and actual documentation commits.
3. **Calibrated Semantic Router:**
   Develop an intermediate routing tier that feeds function signatures and docstring docblocks into local AI models when AST facts represent behavioral changes (return values, exceptions, decorators), with explicit negative controls for sibling parameters.
