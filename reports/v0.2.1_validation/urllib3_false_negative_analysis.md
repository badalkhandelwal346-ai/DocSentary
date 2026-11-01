# Pipeline Trace & Root-Cause Failure Analysis: `BLIND-URLLIB3-01`

**Scenario ID:** `BLIND-URLLIB3-01`  
**Repository:** `urllib3/urllib3`  
**Evaluation Commit:** Frozen DocSentry v0.2 (`cb6234f`)  
**Claimed Drift Type:** `constant_value_change`  
**Ground-Truth Expectation:** True Positive (Doc drift detected)  
**Actual Result:** False Negative (Missed by both Deterministic and Selective Hybrid)

---

## 1. Executive Summary

In the 8-scenario blind evaluation across four previously unseen repositories, DocSentry achieved 7/8 passing scenarios (Precision: 100%, Recall: 75%, F1: 0.8571). The sole false negative was `BLIND-URLLIB3-01`.

This forensic analysis traces the execution of `BLIND-URLLIB3-01` step by step through all stages of the DocSentry v0.2 pipeline:
1. AST Code Fact Extraction
2. Markdown Documentation Span Parsing
3. Code-to-Doc Candidate Retrieval & Scoring
4. Deterministic Rule Evaluation
5. LLM Router & Semantic Model Verifier
6. Evidence Snapshot Validation

**Primary Finding:** The failure is conclusively isolated to **Stage 3: Candidate Retrieval / Semantic Association**. 
The candidate mapper scored the pair at **1.0**, falling well below the minimum candidate retention threshold of **4.0**. Because the candidate link was filtered out at Stage 3, neither the deterministic rule engine (`PY-CONST-005`) nor the local LLM (`qwen3:8b`) ever received the pair for evaluation.

---

## 2. End-to-End Pipeline Trace

### Step 1: Code Fact Extraction (AST)
- **Input File:** `urllib3/util/timeout.py`
- **Diff:**
  ```diff
  -DEFAULT_TIMEOUT = 3.0
  +DEFAULT_TIMEOUT = 5.0
  ```
- **Extracted Fact:**
  - `fact_id`: `fact-urllib3/util/timeout.py-DEFAULT_TIMEOUT`
  - `path`: `urllib3/util/timeout.py`
  - `kind`: `constant_changed`
  - `symbol`: `DEFAULT_TIMEOUT`
  - `member`: `DEFAULT_TIMEOUT`
  - `before`: `"3.0"`
  - `after`: `"5.0"`
  - `category`: `"syntactic"`
- **Evaluation:** **PASSED**. The Python AST extractor cleanly detected the module-level constant assignment change and accurately recorded old and new literal values.

---

### Step 2: Documentation Parsing (Markdown)
- **Input File:** `docs/user-guide.md`
- **Documentation Text:**
  ```markdown
  # User Guide

  Default pool timeout is set to 3.0 seconds.
  ```
- **Extracted DocSpan:**
  - `span_id`: `span-docs/user-guide.md-3-3`
  - `path`: `docs/user-guide.md`
  - `line_start`: 3
  - `line_end`: 3
  - `raw_text`: `"Default pool timeout is set to 3.0 seconds."`
  - `block_type`: `"paragraph"`
  - `claim_type`: `"active_assertion"`
  - `heading_path`: `["User Guide"]`
  - `inline_code`: `[]` (empty; the text did not format tokens in backticks)
- **Evaluation:** **PASSED**. Markdown block extraction, heading context, and claim classification (`active_assertion`) operated properly.

---

### Step 3: Candidate Retrieval & Scoring
- **Scoring Function:** `CandidateMapper.map()` (`min_score = 4.0`, `top_k = 5`)
- **Score Breakdown for `(DEFAULT_TIMEOUT, "Default pool timeout is set to 3.0 seconds.")`:**
  1. *Exact qualified symbol match (`DEFAULT_TIMEOUT` in text):* **0.0** (Doc text does not contain `"DEFAULT_TIMEOUT"`).
  2. *Exact unqualified symbol match (`DEFAULT_TIMEOUT` in text or inline code):* **0.0** (No match).
  3. *Exact parameter or flag match:* **0.0** (`member` is `"DEFAULT_TIMEOUT"`, no match).
  4. *Source path link match:* **0.0** (No hyperlinks in doc).
  5. *Heading keyword match:* **0.0** (`{'default', 'timeout'} & {'user', 'guide'} == empty`).
  6. *Code fence signature match:* **0.0** (Paragraph block, not fence).
  7. *Value match (`"3.0"` in text):* **+1.0** (`re.search(r"\b3.0\b", span_text)` matches `"3.0"`).
  8. *Behavioral semantic keyword match:* **0.0** (`fact.kind` is `"constant_changed"`, not `return_changed`, `exception_changed`, or `behavior_changed`).
- **Total Calculated Score:** **1.0**
- **Threshold Check:** `1.0 >= 4.0` $\rightarrow$ **FALSE**.
- **Outcome:** The candidate pair was discarded. `candidates` list returned empty (`len = 0`).
- **Evaluation:** **FAILED**. Severe vocabulary and semantic gap. The doc used prose terminology (*"pool timeout"*) rather than identifier code tokens (*"`DEFAULT_TIMEOUT`"*).

---

### Step 4: Deterministic Rule Engine
- **Engine Execution:** `DeterministicRuleEngine.evaluate(code_facts, doc_spans, candidates)`
- **Input Candidates:** Empty list (`[]`).
- **Evaluated Rules:** None.
- **Hypothetical Evaluation (If candidate had been forced through):**
  - Rule `PY-CONST-005` in `docsentry/rules/constants.py` requires:
    ```python
    mentions_name = bool(
        constant_name in doc_span.inline_code
        or re.search(rf"\b{re.escape(constant_name)}\b", span_text)
        or any(p in doc_span.inline_code or re.search(rf"\b{re.escape(str(p))}\b", span_text) for p in linked_params)
    )
    ```
  - Because `constant_name` (`"DEFAULT_TIMEOUT"`) is not in the text, `mentions_name` evaluates to `False`.
  - Therefore, `PY-CONST-005` would have returned `None` even if the candidate reached the rule engine.
- **Evaluation:** **INACTIVE** due to upstream filtering; structurally incapable of matching prose without exact identifier tokens.

---

### Step 5: LLM Router & Semantic Model Verifier
- **Verifier Execution:** `SemanticModelVerifier.verify_candidates(...)`
- **Invocations:** **0**.
- **Hypothetical Evaluation (If candidate had reached verifier):**
  - Routing condition:
    ```python
    is_behavioral = getattr(fact, "category", "syntactic") == "behavioral"
    is_strong_semantic = link.score >= 5.0 and span_claim == "active_assertion"
    if not (is_behavioral or is_strong_semantic):
        continue
    ```
  - `fact.category` is `"syntactic"`, and `link.score` was 1.0 (< 5.0).
  - The verifier would have bypassed LLM invocation.
- **Evaluation:** **INACTIVE**.

---

### Step 6: Evidence Snapshot Validation
- **Validation Execution:** `EvidenceValidator.validate_findings(...)`
- **Findings Received:** Empty list (`[]`).
- **Evaluation:** **INACTIVE**.

---

## 3. Precise Failure Classification

| Question | Answer | Details |
|---|---|---|
| 1. Was relevant code fact extracted? | **YES** | AST extracted `constant_changed` for `DEFAULT_TIMEOUT` (`3.0` $\rightarrow$ `5.0`). |
| 2. Was doc claim parsed correctly? | **YES** | `active_assertion` paragraph parsed at `docs/user-guide.md:3-3`. |
| 3. Did candidate retrieval associate the two? | **NO** | 0 candidate links produced. |
| 4. What relevance score was assigned? | **1.0** | +1.0 for literal value match (`"3.0"`). |
| 5. Was candidate filtered before Qwen? | **YES** | Discarded at retrieval (`1.0 < 4.0`), and routing filter (`1.0 < 5.0`). |
| 6. Did Qwen reason incorrectly or abstain? | **N/A** | Qwen was never invoked (0 calls). |
| 7. Did evidence validation reject finding? | **N/A** | No finding reached validation. |
| 8. Was final report incorrect despite valid intermediate finding? | **NO** | No intermediate finding was ever produced. |

**Failure Stage:** **Stage 3: Candidate Retrieval / Semantic Association Failure**.

---

## 4. Root Cause Analysis: The Vocabulary Gap vs. Negative Controls

The failure stems from a fundamental dilemma in documentation drift detection:
- **The Case at Hand:** The documentation describes a functional behavior in human language (*"Default pool timeout is set to 3.0 seconds."*) without mentioning the Python identifier `DEFAULT_TIMEOUT`.
- **The Naive Temptation:** One could lower `min_score` to 1.0, or award high scores whenever individual token parts (`"default"` and `"timeout"`) appear in the text.
- **The False-Positive Trap (Adversarial Negative Controls):**
  If the candidate mapper naively scores any sentence matching tokens `{"default", "timeout"}` and value `"3.0"`:
  ```python
  # Code change:
  DEFAULT_TIMEOUT = 5.0  # previously 3.0

  # Documentation sentences:
  "Default read timeout is set to 3.0 seconds."       # FAILS: Unrelated parameter
  "Default connect timeout is set to 3.0 seconds."    # FAILS: Unrelated parameter
  "Default retry timeout is set to 3.0 seconds."      # FAILS: Unrelated parameter
  ```
  In complex network libraries (including `urllib3`), `DEFAULT_TIMEOUT`, `DEFAULT_RETRIES`, `READ_TIMEOUT`, and `CONNECT_TIMEOUT` frequently co-exist with identical default float values (e.g., `3.0` or `None`).
  A naive semantic or token-overlap retriever would associate changes in `DEFAULT_TIMEOUT` with documented statements about `read timeout`, generating catastrophic **False Positive drift alerts**.

---

## 5. Principled Future Architectural Solution

To resolve indirect conceptual drift like `BLIND-URLLIB3-01` without introducing false positives, the system requires two non-breaking structural enhancements (for v0.3):

1. **AST Call-Graph & Default Propagation:**
   Rather than treating module constants in isolation, the code extractor should trace where `DEFAULT_TIMEOUT` flows. If `DEFAULT_TIMEOUT` is passed as the default value to `PoolManager.__init__(timeout=DEFAULT_TIMEOUT)` or `HTTPConnectionPool(timeout=DEFAULT_TIMEOUT)`, the fact should record `linked_symbols=["PoolManager", "HTTPConnectionPool", "pool_timeout"]`.
   This enables the candidate mapper's existing `linked_params` mechanism to score the doc span at **6.0+**, without broad fuzzy matching.

2. **Sibling Disambiguation in Candidate Scoring:**
   When token-overlap matching is employed for compound terms (`default` + `timeout`), the system must extract all sibling constants in the same scope (`READ_TIMEOUT`, `CONNECT_TIMEOUT`). If the doc span contains a modifier corresponding to a different sibling (e.g. `"read"`), the candidate must be penalized (-6.0) and rejected.

---

## 6. Conclusion

The false negative in `BLIND-URLLIB3-01` is not an AI reasoning error, nor a bug in evidence validation. It is a classic information-retrieval boundary: deterministic candidate retrieval refused to link an unqualified prose phrase to an exact code symbol.

Under DocSentry's design principles, **abstention is strictly preferable to speculative hallucination**. The v0.2 implementation correctly preserved 100% precision across all negative controls rather than relaxing thresholds to capture this single edge case.
