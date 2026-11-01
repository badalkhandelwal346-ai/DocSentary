# DocSentry v0.2.1: Blind Benchmark Verification (Deterministic vs. Hybrid)

**Evaluation Date:** 2026-11-01  
**Hardware Profile:** Apple Silicon M4 MacBook Pro, 16GB Unified Memory  
**Target Model:** Local Open-Weight `qwen3:8b` via Ollama  
**Evaluation Scope:** 8 Scenarios across 4 Previously Unseen Repositories (`urllib3`, `marshmallow`, `aiohttp`, `starlette`)  
**Implementation Baseline:** Frozen v0.2 (`cb6234f`)

---

## 1. Executive Summary & Core Finding

A rigorous, independent evaluation of DocSentry v0.2 was executed on the exact same 8 blind scenarios under two configurations:
- **Configuration A:** Deterministic-Only (all LLM invocations disabled; pure AST rules and candidate mapping)
- **Configuration B:** Selective Hybrid (`qwen3:8b` enabled via Ollama with unchanged routing thresholds)

### Critical Result: Zero Incremental AI Contribution on Blind Set
On this 8-scenario blind benchmark across four unseen repositories:
- **Deterministic-only detected 3 out of 4 positive drift cases (75.0% recall, 100.0% precision, F1: 0.8571).**
- **Selective Hybrid detected the exact same 3 cases (75.0% recall, 100.0% precision, F1: 0.8571).**
- **Qwen3-8B model invocations on the blind dataset:** **0 invocations**.
- **Incremental AI Contribution:** **0.0%**.

The deterministic engine alone established 100% of the detection capability on this blind dataset. Because the detected drifts were structural changes (parameter removal in Marshmallow, default value change in AIOHTTP, and symbol removal in Starlette), deterministic rules diagnosed them instantly without routing to the LLM. Both configurations failed to detect `BLIND-URLLIB3-01` due to an upstream candidate retrieval vocabulary gap.

---

## 2. Aggregate Benchmark Metrics Comparison

| Metric | Configuration A: Deterministic-Only | Configuration B: Selective Hybrid (`qwen3:8b`) | Difference / AI Delta | Metric Interpretation & Denominators |
|:---|:---:|:---:|:---:|:---|
| **Total Scenarios** | 8 | 8 | 0 | 4 Positive drift cases, 4 Negative controls |
| **Passed Scenarios** | 7 (87.5%) | 7 (87.5%) | 0 | Correctly diagnosed drift or respected negative control |
| **True Positives (TP)** | 3 | 3 | 0 | `BLIND-MARSHMALLOW-01`, `BLIND-AIOHTTP-01`, `BLIND-STARLETTE-01` |
| **False Positives (FP)** | **0** | **0** | 0 | Zero false alarms on all 4 negative controls |
| **True Negatives (TN)** | 4 | 4 | 0 | 100% rejection of negative controls |
| **False Negatives (FN)** | 1 | 1 | 0 | `BLIND-URLLIB3-01` missed by both engines |
| **Precision** | **100.0%** (3/3) | **100.0%** (3/3) | 0.0% | $\frac{\text{TP}}{\text{TP} + \text{FP}}$ |
| **Recall** | **75.0%** (3/4) | **75.0%** (3/4) | 0.0% | $\frac{\text{TP}}{\text{TP} + \text{FN}}$ |
| **Specificity** | **100.0%** (4/4) | **100.0%** (4/4) | 0.0% | $\frac{\text{TN}}{\text{TN} + \text{FP}}$ |
| **F1 Score** | **0.8571** | **0.8571** | 0.0000 | Harmonic mean of precision and recall |
| **Conditional Location Accuracy** | **100.0%** (3/3) | **100.0%** (3/3) | 0.0% | $\frac{\text{Exact Doc Matches}}{\text{Detected Positives}}$ (exact sentence level) |
| **Conditional Attribution Accuracy** | **100.0%** (3/3) | **100.0%** (3/3) | 0.0% | $\frac{\text{Exact Code Matches}}{\text{Detected Positives}}$ (exact source symbol) |
| **Evidence Validation Pass Rate** | **100.0%** (3/3) | **100.0%** (3/3) | 0.0% | 100% of findings backed by verified Git snapshot lines |
| **Average Scan Latency** | 221.9 ms | 219.4 ms | -2.5 ms | Sub-second local execution |
| **Median Scan Latency** | 224.9 ms | 217.2 ms | -7.7 ms | Consistent execution time |

---

## 3. Case-by-Case Forensic Audit & Comparison Table

| Scenario ID | Repository | Ground Truth | Deterministic Outcome | Hybrid Outcome | Model Calls | AI Found More? | AI FP? | Latency (Det / Hyb) |
|:---|:---|:---:|:---|:---|:---:|:---:|:---:|:---:|
| `BLIND-URLLIB3-01` | `urllib3/urllib3` | Drift (`constant_value_change`) | **MISSED (FN)** (Score: 0.0, Rule: None) | **MISSED (FN)** (Score: 0.0, Rule: None) | 0 | No | No | 225.0 ms / 217.2 ms |
| `BLIND-URLLIB3-NC1` | `urllib3/urllib3` | Control (`negative_control_refactor`) | **PASS (TN)** (No drift detected) | **PASS (TN)** (No drift detected) | 0 | No | No | 235.0 ms / 219.3 ms |
| `BLIND-MARSHMALLOW-01` | `marshmallow-code/marshmallow` | Drift (`parameter_removed`) | **DETECTED (TP)** (`PY-PARAM-002`) | **DETECTED (TP)** (`PY-PARAM-002`) | 0 | No | No | 223.4 ms / 226.8 ms |
| `BLIND-MARSHMALLOW-NC1` | `marshmallow-code/marshmallow` | Control (`negative_control_refactor`) | **PASS (TN)** (No drift detected) | **PASS (TN)** (No drift detected) | 0 | No | No | 203.7 ms / 209.8 ms |
| `BLIND-AIOHTTP-01` | `aio-libs/aiohttp` | Drift (`default_value_change`) | **DETECTED (TP)** (`PY-DEFAULT-001`) | **DETECTED (TP)** (`PY-DEFAULT-001`) | 0 | No | No | 216.1 ms / 214.4 ms |
| `BLIND-AIOHTTP-NC1` | `aio-libs/aiohttp` | Control (`negative_control_refactor`) | **PASS (TN)** (No drift detected) | **PASS (TN)** (No drift detected) | 0 | No | No | 209.5 ms / 206.0 ms |
| `BLIND-STARLETTE-01` | `encode/starlette` | Drift (`symbol_removed`) | **DETECTED (TP)** (`PY-SYMBOL-003`) | **DETECTED (TP)** (`PY-SYMBOL-003`) | 0 | No | No | 230.7 ms / 249.0 ms |
| `BLIND-STARLETTE-NC1` | `encode/starlette` | Control (`negative_control_refactor`) | **PASS (TN)** (No drift detected) | **PASS (TN)** (No drift detected) | 0 | No | No | 232.0 ms / 212.8 ms |

---

## 4. Per-Scenario Detailed Evidence & Findings

### Scenario 1: `BLIND-URLLIB3-01` (`urllib3/urllib3`)
- **Code Change:** `DEFAULT_TIMEOUT = 3.0` $\rightarrow$ `DEFAULT_TIMEOUT = 5.0` in `urllib3/util/timeout.py`.
- **Doc Sentence:** `"Default pool timeout is set to 3.0 seconds."` in `docs/user-guide.md`.
- **Deterministic Result:** Missed. Code fact `constant_changed(DEFAULT_TIMEOUT, 3.0 -> 5.0)` was extracted, but candidate mapper scored 0.0 because the documentation text referred to `"pool timeout"` without mentioning the exact token `"DEFAULT_TIMEOUT"`.
- **Hybrid Result:** Missed. Because candidate relevance was below the minimum candidate score threshold (4.0), no candidate was created to send to Qwen.
- **Verdict:** True Positive missed by both configurations (False Negative).

### Scenario 2: `BLIND-URLLIB3-NC1` (`urllib3/urllib3`)
- **Code Change:** Internal buffer allocation comment added to `_get_conn()` in `urllib3/connectionpool.py`.
- **Doc Sentence:** `"Connection pools maintain persistent HTTP socket connections."` in `docs/advanced.md`.
- **Deterministic Result:** Clean pass. No AST code facts modified.
- **Hybrid Result:** Clean pass. 0 model calls, 0 false alarms.
- **Verdict:** Sound True Negative.

### Scenario 3: `BLIND-MARSHMALLOW-01` (`marshmallow-code/marshmallow`)
- **Code Change:** `Field.__init__(self, default=None, missing=None, required=False)` $\rightarrow$ `missing` parameter removed in favor of `load_default` in `marshmallow/fields.py`.
- **Doc Sentence:** `"Provide a fallback value when deserializing using the missing argument."` in `docs/quickstart.md`.
- **Deterministic Result:** Detected via Rule `PY-PARAM-002` (Removed parameter `missing`). Exact line and symbol matched.
- **Hybrid Result:** Detected via Rule `PY-PARAM-002`. Because deterministic diagnosis was complete, hybrid routing safely bypassed LLM invocation.
- **Verdict:** Valid True Positive detected deterministically.

### Scenario 4: `BLIND-MARSHMALLOW-NC1` (`marshmallow-code/marshmallow`)
- **Code Change:** Fast-path check `if not data: return {}` added to `Schema.validate()` in `marshmallow/schema.py`.
- **Doc Sentence:** `"Schemas validate dictionary payloads against registered field types."` in `docs/extending.md`.
- **Deterministic Result:** Clean pass. Non-breaking internal implementation optimization.
- **Hybrid Result:** Clean pass. 0 false alarms.
- **Verdict:** Sound True Negative.

### Scenario 5: `BLIND-AIOHTTP-01` (`aio-libs/aiohttp`)
- **Code Change:** `ClientSession.__init__(timeout: int = 300)` $\rightarrow$ `timeout: int = 60` in `aiohttp/client.py`.
- **Doc Sentence:** `"Session connection timeout defaults to 300 seconds."` in `docs/client_quickstart.md`.
- **Deterministic Result:** Detected via Rule `PY-DEFAULT-001` (Stale default `300` $\rightarrow$ `60`). Exact line and symbol matched.
- **Hybrid Result:** Detected via Rule `PY-DEFAULT-001`.
- **Verdict:** Valid True Positive detected deterministically.

### Scenario 6: `BLIND-AIOHTTP-NC1` (`aio-libs/aiohttp`)
- **Code Change:** Route table docstring comment added in `aiohttp/web_app.py`.
- **Doc Sentence:** `"Applications manage request routing through the router interface."` in `docs/web_reference.md`.
- **Deterministic Result:** Clean pass.
- **Hybrid Result:** Clean pass.
- **Verdict:** Sound True Negative.

### Scenario 7: `BLIND-STARLETTE-01` (`encode/starlette`)
- **Code Change:** Class `BaseHTTPMiddleware` removed from `starlette/middleware/base.py`.
- **Doc Sentence:** `"Wrap ASGI apps with BaseHTTPMiddleware to process streaming requests."` in `docs/middleware.md`.
- **Deterministic Result:** Detected via Rule `PY-SYMBOL-003` (Removed symbol `BaseHTTPMiddleware`). Exact line and symbol matched.
- **Hybrid Result:** Detected via Rule `PY-SYMBOL-003`.
- **Verdict:** Valid True Positive detected deterministically.

### Scenario 8: `BLIND-STARLETTE-NC1` (`encode/starlette`)
- **Code Change:** Internal comment added in `JSONResponse` in `starlette/responses.py`.
- **Doc Sentence:** `"JSONResponse automatically serializes dictionaries to JSON."` in `docs/responses.md`.
- **Deterministic Result:** Clean pass.
- **Hybrid Result:** Clean pass.
- **Verdict:** Sound True Negative.

---

## 5. Architectural Evaluation & Limitations

1. **Deterministic Rules Dominate Syntactic Drifts:** For parameter removals, default changes, and removed symbols, deterministic AST rules achieve 100% precision with sub-millisecond execution. Using an LLM for these categories adds latency and risk with zero incremental detection benefit.
2. **AI Added No Value on this Blind Set:** Because all 4 positive scenarios in this specific blind dataset were syntactic/structural drifts (and not behavioral contract invalidations), Qwen3-8B had no opportunities to provide incremental detection.
3. **Retrieval Remains the Single Point of Failure:** In `BLIND-URLLIB3-01`, the failure was entirely located in the candidate retrieval stage. If candidate retrieval does not associate `DEFAULT_TIMEOUT` with `"pool timeout"`, neither deterministic rules nor LLM reasoning will ever evaluate the candidate.
