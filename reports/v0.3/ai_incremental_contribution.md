# DocSentry v0.3: Verified Incremental AI Contribution Analysis

**Evaluation Target:** Quantifying the True Incremental Contribution of Local `qwen3:8b` beyond Deterministic Analysis  
**Date:** 2026-11-01  
**Hardware:** MacBook Pro M4 (16GB Unified Memory), Python 3.14.2, Ollama with local `qwen3:8b`  
**Evaluation Scope:** 48 Authentic Benchmark Scenarios across 11 Repositories

---

## 1. Executive Summary

A critical standard established in the independent ground-truth audit is:
> **Do not claim AI incremental contribution unless the AI-enabled system detects independently verified cases missed by the deterministic system.**

In earlier versions of DocSentry (v0.1 / v0.2), incremental AI contribution on blind repositories was 0.0% because the blind scenarios were purely syntactic.

In DocSentry v0.3, across the 48 authentic real-world cases, local Qwen3-8B achieved **four independently verified incremental detections** that pure deterministic AST analysis could not catch:
1. **`REAL-REQUESTS-01` (`psf/requests` PR #2258):** Procedural drift where additive `json=` support superseded documented manual serialization.
2. **`REAL-URLLIB3-02` (`urllib3/urllib3` PR #2168):** Conceptual constant drift where removing TLS 1.0 ciphers contradicted high-level prose without an exact literal string match.
3. **`REAL-URLLIB3-03` (`urllib3/urllib3` PR #1950):** Behavioral return value shift where `HTTPResponse.read()` returned `b""` instead of `None` on empty bodies.
4. **`REAL-MARSHMALLOW-01` (`marshmallow-code/marshmallow` PR #789 — HELD-OUT TEST):** Breaking return contract shift where `Schema.dump()` changed from returning a 2-tuple `(result, errors)` to returning `result` directly, breaking documented tuple unpacking.

Most importantly, this capability was achieved with **0 AI-generated false positives** and **100% snapshot evidence validity**.

---

## 2. Formal Metric: Verified AI Incremental Contribution

The required formula is:
$$\text{AI Incremental Value} = \frac{\text{Verified AI-Only Detections}}{\text{Independently Verified Positive Scenarios}}$$

### A. Across All Authentic Verified Positive Cases (26 Positive Scenarios)
- Total Positive Cases: 26
- Detected by Deterministic Engine: 16
- Detected by Selective Hybrid: 20
- Verified AI-Only Detections: **4**

$$\text{AI Incremental Value}_{\text{all}} = \frac{4}{26} = \mathbf{15.38\%}$$

### B. On the Untouched Held-Out Test Partition (12 Positive Scenarios)
- Total Positive Cases in Held-Out Set: 12
- Detected by Deterministic: 6
- Detected by Selective Hybrid: 7
- Verified AI-Only Detections: **1** (`REAL-MARSHMALLOW-01`)

$$\text{AI Incremental Value}_{\text{held-out}} = \frac{1}{12} = \mathbf{8.33\%}$$

*(Excluding the 3 questionably phrased FastAPI cases from the denominator: $\frac{1}{9} = \mathbf{11.11\%}$)*

---

## 3. Forensic Breakdown of the Four AI Victories

| Scenario ID | Repository | Code Fact | Documentation Assertion | Why Deterministic Failed | Why Qwen3-8B Succeeded |
|---|---|---|---|---|---|
| **`REAL-REQUESTS-01`** | `psf/requests` | `parameter_added` (`json`) | *"To send JSON, explicitly serialize with `data=json.dumps(payload)`"* | Parameter additions are backward-compatible; syntactic rules do not flag them. | Recognized procedural drift: native `json=` parameter makes manual serialization obsolete. |
| **`REAL-URLLIB3-02`** | `urllib3/urllib3` | `constant_changed` (`DEFAULT_CIPHERS`) | *"By default, DEFAULT_CIPHERS permits TLS 1.0 and 1.1 fallback suites."* | Rule `PY-CONST-005` looks for the raw OpenSSL cipher string literal, not semantic prose. | Understood that removing `TLS10` from the cipher string directly contradicts the claim that TLS 1.0 is permitted. |
| **`REAL-URLLIB3-03`** | `urllib3/urllib3` | `return_changed` (`read()`) | *"Calling response.read() on an empty body returns None."* | Syntactic rules focus on parameters and symbols; return changes are behavioral. | Recognized semantic contradiction: `read()` now returns `b""`, directly violating the documented `None` contract. |
| **`REAL-MARSHMALLOW-01`** | `marshmallow` *(Held-Out)* | `return_changed` (`dump()`) | *"result, errors = schema.dump(user) unpacks the serialized dictionary and error collection."* | Doc describes 2-tuple unpacking syntax rather than literal function signature equality. | Recognized that returning a dictionary directly breaks the documented 2-variable unpacking pattern. |

---

## 4. Secondary AI Reliability & Safety Metrics

| Metric | Result | Target Benchmark Standard |
|---|---|---|
| **AI-Only False Positives** | **0** | **0 (Zero-Tolerance)** |
| **AI-Only False Negatives** | **0** | Must not introduce new misses |
| **AI Invocations on Negative Controls** | **0** | Gating filter must block benign PRs |
| **Evidence Validation Pass Rate** | **100.0%** | Zero hallucinations permitted |
| **Average Latency per AI Invocation** | **1,820 ms** | $< 5,000\text{ ms}$ on local Apple M4 |
| **Peak Memory Consumption** | **4.8 GB** | $< 16\text{ GB}$ (Single model in Ollama) |

---

## 5. Drift Categorization & Honest Reporting

To prevent misleading claims, DocSentry strictly categorizes drift findings:

1. **Breaking Factual Drift (Severe):**
   Code behavior violates an explicit documented contract, causing user code to crash or fail silently (`REAL-URLLIB3-02`, `REAL-URLLIB3-03`, `REAL-MARSHMALLOW-01`).
   - Detected by Hybrid: **3 cases**
   - Verified Severity: High / Critical

2. **Procedural / Advisory Drift (Medium):**
   Existing code still works, but documentation recommends obsolete, inefficient, or superseded patterns (`REAL-REQUESTS-01`).
   - Detected by Hybrid: **1 case**
   - Verified Severity: Medium

3. **Incomplete Capabilities (Informational):**
   Additive features where existing documentation remains factually accurate.
   - Handled via `claim_status: incomplete_new_capability` $\rightarrow$ Evaluated as `NO_DRIFT` to prevent alert fatigue.

---

## 6. Conclusion

In DocSentry v0.3, AI reasoning is no longer a cosmetic wrapper or a zero-contribution benchmark footnote.

By combining **deterministic AST extraction for facts**, **relationship-aware candidate routing for safety**, and **local Qwen3-8B for semantic interpretation**, DocSentry delivers measurable, reproducible, and verifiable intelligence on complex documentation drift that static analysis alone cannot solve.
