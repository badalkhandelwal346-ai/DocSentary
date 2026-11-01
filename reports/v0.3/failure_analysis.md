# DocSentry v0.3: Stage-by-Stage Failure Analysis & Diagnostic Report

**Evaluation Target:** Unchanged Baseline on Authentic Benchmark (Dev + Val Partitions, 26 Cases)  
**Date:** 2026-11-01  
**Configurations Evaluated:**  
- Configuration A: Unchanged Deterministic Engine (Passed: 22/26, 84.6%, FP: 0, FN: 4)  
- Configuration B: Unchanged Selective Hybrid (`qwen3:8b`) (Passed: 26/26, 100.0%, FP: 0, FN: 0)

---

## 1. Executive Summary & Diagnostic Overview

To ensure that improvements in v0.3 target real engineering bottlenecks rather than speculative tweaks, all 26 development and validation benchmark cases were traced through the 11 sequential stages of the DocSentry pipeline:
1. Git diff inspection
2. Code fact extraction (AST)
3. Documentation parsing (Markdown)
4. Claim classification
5. Candidate retrieval
6. Relevance scoring
7. Evidence construction
8. AI routing
9. Qwen3-8B inference
10. Evidence snapshot validation
11. Final finding generation

### Core Finding
- **Zero False Positives Across All 13 Negative Controls:**
  Every negative control (refactoring, test-only, and in-sync documentation) was correctly identified as `NO_DRIFT` by both configurations.
- **The Deterministic Bottleneck:**
  All four false negatives in the deterministic engine (`REAL-HTTPX-03`, `REAL-REQUESTS-01`, `REAL-URLLIB3-02`, and `REAL-URLLIB3-03`) passed AST extraction, Markdown parsing, and Candidate Retrieval with high scores ($8.0$ to $16.0$), but failed at **Stage 5: Rule Evaluation** because deterministic rules strictly require literal token equivalence (e.g. matching an exact 80-character cipher string or exact parameter deletion).
- **The Hybrid Breakthrough:**
  When candidates passed into the bounded `SemanticModelVerifier`, Qwen3-8B correctly interpreted the semantic meaning behind the code changes, turning all 4 deterministic false negatives into verified true positives without a single false positive on negative controls.

---

## 2. Stage-by-Stage Forensic Breakdown of Missed Cases

### Case 1: `REAL-URLLIB3-02` (Removal of TLS 1.0 Legacy Ciphers)
- **Code Diff:** `DEFAULT_CIPHERS = '...:TLS10'` $\rightarrow$ `DEFAULT_CIPHERS = '...'` in `urllib3/util/ssl_.py`.
- **Documentation Text:** *"By default, DEFAULT_CIPHERS permits TLS 1.0 and 1.1 fallback suites."*
- **Stage 1 (Git Diff):** PASSED. Clean diff hunk.
- **Stage 2 (Code Fact Extraction):** PASSED. Extracted `constant_changed` on `DEFAULT_CIPHERS`.
- **Stage 3 (Documentation Parsing):** PASSED. Extracted line 3 `active_assertion`.
- **Stage 4 (Claim Classification):** PASSED. Identified as active factual assertion.
- **Stage 5 & 6 (Candidate Retrieval & Scoring):** PASSED with score **16.0** (`exact_qualified_symbol_match` + `exact_parameter_or_flag_match`).
- **Stage 7 (Deterministic Rules Engine):** **FAILED (False Negative).**
  - Rule `PY-CONST-005` checks whether `code_fact.before` (the full raw cipher string) is contained in the doc text.
  - Because the doc author described the *semantic capability* (*"permits TLS 1.0"*) rather than copying the raw OpenSSL cipher string, the rule returned `None`.
- **Stage 8 (AI Routing):** PASSED. Routed to Qwen3-8B because candidate score was $16.0 \ge 5.0$ and claim was `active_assertion`.
- **Stage 9 (Qwen Inference):** PASSED. Qwen reasoned that removing TLS10 from `DEFAULT_CIPHERS` directly contradicts the documented claim that TLS 1.0 is permitted by default.
- **Stage 10 & 11 (Evidence Validation & Finding):** PASSED. Generated `PY-BEHAVIOR-006` with 100% evidence validity.

---

### Case 2: `REAL-URLLIB3-03` (Return Value Contract on Empty Stream)
- **Code Diff:** `HTTPResponse.read()` changed from returning `None` on empty stream to returning `b""`.
- **Documentation Text:** *"Calling response.read() on an empty body returns None."*
- **Stage 1 to 4:** PASSED. Code fact extracted as `return_changed` (`category="behavioral"`), doc span parsed as `active_assertion`.
- **Stage 5 & 6:** PASSED with score **13.0** (`exact_unqualified_symbol_match` + `return_semantic_match`).
- **Stage 7 (Deterministic Rules Engine):** **FAILED (False Negative).**
  - No deterministic rule in v0.2 evaluated `return_changed` facts against Markdown doc spans.
- **Stage 8 (AI Routing):** PASSED. Routed because `category == "behavioral"`.
- **Stage 9 (Qwen Inference):** PASSED. Qwen correctly identified direct contradiction (`None` vs `b""`).
- **Stage 10 & 11:** PASSED. Verified finding emitted.

---

### Case 3: `REAL-REQUESTS-01` (Additive `json=` Parameter Superseding Serialization)
- **Code Diff:** `def post(url, data=None, json=None)` in `requests/api.py`.
- **Documentation Text:** *"To send JSON, explicitly serialize the string with data=json.dumps(payload)."*
- **Stage 1 to 4:** PASSED. Fact extracted as `parameter_added`, doc parsed as `active_assertion`.
- **Stage 5 & 6:** PASSED with score **9.0** (`exact_parameter_or_flag_match` + `heading_keyword_match`).
- **Stage 7 (Deterministic Rules Engine):** **FAILED (False Negative).**
  - Parameter additions are backward-compatible and therefore do not trigger `PY-PARAM-002` (parameter removed) or `PY-DEFAULT-001`.
- **Stage 8 & 9 (AI Routing & Inference):** PASSED. Qwen recognized procedural drift (native `json=` parameter obsoleted manual serialization).

---

### Case 4: `REAL-HTTPX-03` (Keyword Forwarding in `Response.json()`)
- **Code Diff:** `def json(self, **kwargs)` added to `Response.json`.
- **Documentation Text:** *"response.json() parses payload strictly with default JSONDecoder."*
- **Stage 1 to 6:** PASSED with score **8.0**.
- **Stage 7 (Deterministic Rules):** **FAILED.** Syntactic rules do not flag additive kwargs.
- **Stage 8 & 9 (AI Routing & Inference):** PASSED. Qwen flagged potential drift on strict parsing assertions.

---

## 3. Failure Stage Diagnostic Matrix

| Scenario ID | Repository | Code Change Kind | Failure Stage | Root Cause Mechanism | Successfully Recovered By |
|---|---|---|---|---|---|
| `REAL-HTTPX-03` | `encode/httpx` | `parameter_added` | Stage 7 (Rules Engine) | Syntactic rules ignore additive `**kwargs` | Qwen3-8B (`PY-BEHAVIOR-006`) |
| `REAL-REQUESTS-01` | `psf/requests` | `parameter_added` | Stage 7 (Rules Engine) | Procedural drift not capturable by AST equality | Qwen3-8B (`PY-BEHAVIOR-006`) |
| `REAL-URLLIB3-02` | `urllib3/urllib3` | `constant_changed` | Stage 7 (Rules Engine) | Literal quote mismatch (OpenSSL string vs prose) | Qwen3-8B (`PY-BEHAVIOR-006`) |
| `REAL-URLLIB3-03` | `urllib3/urllib3` | `return_changed` | Stage 7 (Rules Engine) | No deterministic rule for return value diffs | Qwen3-8B (`PY-BEHAVIOR-006`) |

---

## 4. Key Takeaways for v0.3 Architecture

1. **Deterministic Rules Need Return-Value Support:**
   When AST detects `return_changed` (e.g. `before="None"`, `after="b''"`), a deterministic rule (`PY-RETURN-007`) should evaluate whether the doc span explicitly claims `"returns None"` or `"returns empty list"`. This recovers return-value drift deterministically without requiring an LLM.
2. **AST Call-Graph Propagation:**
   Constants like `DEFAULT_TIMEOUT` and `DEFAULT_CIPHERS` must carry call-site linkage so that candidate retrieval connects them to their consuming classes (`PoolManager`, `SSLContext`).
3. **Structured Bounded AI Reasoning:**
   The hybrid engine demonstrated 100% precision and zero false positives because it is only invoked when candidate links are strong ($\ge 5.0$). This routing contract must remain strictly intact in v0.3.
