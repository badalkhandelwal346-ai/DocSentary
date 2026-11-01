# DocSentry v0.3: Frozen Baseline Report

**Recorded At:** 2026-11-01T05:22:00+05:30  
**Current Git HEAD:** `e8e2ddd`  
**Underlying Engine Commit:** `cb6234f` + regression test harness `ae4c395`  
**Hardware & Environment:** MacBook Pro M4 (16GB Unified Memory), Python 3.14.2, Ollama with local `qwen3:8b`  
**Purpose:** Strict baseline record to benchmark all v0.3 improvements against.

---

## 1. Existing Evaluation Datasets & Baseline Performance

### A. Verified 25 Historical Benchmark (Reconstructed Upstream Snapshots)
- **Total Cases:** 25 (11 Positive Drift, 14 Negative Controls)
- **Repositories:** `encode/httpx`, `pallets/click`, `fastapi/fastapi`, `psf/requests`, `pallets/flask`, `pydantic/pydantic`, `axios/axios`
- **v0.2 Baseline Metrics:**
  - **Deterministic-Only:**
    - TP: 10, FP: 0, TN: 14, FN: 1
    - Precision: 100.0%, Recall: 90.91%, Specificity: 100.0%, F1 Score: 0.9524
    - Conditional Location Accuracy: 100.0%, Attribution Accuracy: 100.0%
    - Evidence Validation Rate: 100.0%
    - LLM Invocations: 0
  - **Selective Hybrid (`qwen3:8b`):**
    - TP: 11, FP: 0, TN: 14, FN: 0
    - Precision: 100.0%, Recall: 100.0%, Specificity: 100.0%, F1 Score: 1.0000
    - Conditional Location Accuracy: 100.0%, Attribution Accuracy: 100.0%
    - Evidence Validation Rate: 100.0%
    - LLM Invocations: 1 (`REAL-REQUESTS-01`, reclassified as advisory drift)

### B. Fresh Blind Benchmark (Synthetic 8-Case Fixtures)
- **Total Cases:** 8 (4 Positive Drift, 4 Negative Controls)
- **Repositories:** `urllib3/urllib3`, `marshmallow-code/marshmallow`, `aio-libs/aiohttp`, `encode/starlette`
- **Audit Finding:** All 8 cases utilized synthetic mock SHAs (`c101...` to `c108...`) and constructed text fixtures.
- **v0.2 Baseline Metrics:**
  - **Deterministic-Only:**
    - TP: 3, FP: 0, TN: 4, FN: 1 (`BLIND-URLLIB3-01`)
    - Precision: 100.0%, Recall: 75.0%, Specificity: 100.0%, F1 Score: 0.8571
    - Average Latency: 221.9 ms
  - **Selective Hybrid (`qwen3:8b`):**
    - TP: 3, FP: 0, TN: 4, FN: 1 (`BLIND-URLLIB3-01`)
    - Precision: 100.0%, Recall: 75.0%, Specificity: 100.0%, F1 Score: 0.8571
    - Average Latency: 219.4 ms
    - LLM Invocations: 0 (0.0% incremental AI value)

---

## 2. Existing Regression Test Suite
- **Total Tests Passing:** 58 tests in `tests/`
  - Integration: `test_pipeline.py` (1)
  - Replay fixtures: `test_fixtures.py` (6)
  - AST unit tests: `test_ast.py` (5)
  - CLI unit tests: `test_cli.py` (2)
  - Contracts: `test_contracts.py` (4)
  - Evidence adversarial tests: `test_evidence_adversarial.py` (14)
  - Git utilities: `test_git.py` (4)
  - Markdown parser: `test_markdown.py` (2)
  - Rules engine: `test_rules.py` (8)
  - v0.2.1 Regression suite: `test_v021_regression.py` (12)

---

## 3. Verified Baseline Pipeline Constraints
1. **Candidate Mapping Threshold:** `min_score = 4.0` in `CandidateMapper`.
2. **AI Verifier Routing:** Fact must have `category == "behavioral"` OR candidate link must have `score >= 5.0` with `span_claim == "active_assertion"`.
3. **Abstention Guarantee:** Any model failure or ambiguity defaults to `UNCERTAIN` and is omitted from final drift findings, maintaining 100% precision.
