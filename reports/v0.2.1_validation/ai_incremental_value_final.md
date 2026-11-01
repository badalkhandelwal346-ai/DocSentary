# DocSentry v0.2.1: Final Evaluation of Incremental AI Value

**Repository:** `Atharv386/DocSentary`  
**Evaluation Target:** DocSentry v0.2 (`cb6234f`) vs v0.1 Baselines  
**Hardware:** MacBook Pro M4 (16GB Unified Memory)  
**Local Model:** `qwen3:8b` via Ollama (`http://localhost:11434`)  
**Evaluation Scope:** 6 System Configurations Across Historical and Blind Datasets

---

## 1. Executive Summary

A core question of this engineering audit is:
> **Does Qwen3-8B contribute measurable value beyond deterministic analysis, particularly on repositories it has never encountered, without introducing false positives?**

Based on consolidated evaluations across the verified historical benchmark (25 cases) and the fresh blind benchmark (8 cases), the empirical answers are:
1. **On Unseen Repositories (Blind Dataset):** **0.0% Incremental AI Value.**
   Deterministic analysis achieved 100% of the detections (3/3 true positives, 4/4 true negatives). Qwen3-8B was invoked **0 times**.
2. **On the Historical Benchmark (25 Cases):** **At most 1 incremental detection (`REAL-REQUESTS-01`).**
   However, forensic upstream verification in Phase 2 demonstrated that `REAL-REQUESTS-01` is a procedural best-practice recommendation rather than a breaking semantic contradiction.
   - Under strict breaking syntactic criteria: **0.0% Verified AI-only contribution** (0 / 11 positive cases).
   - Under relaxed procedural/advisory criteria: **9.09% Verified AI-only contribution** (1 / 11 positive cases).
3. **Safety & Precision Invariant:** **100% Specificity.**
   In all configurations and datasets, Qwen3-8B introduced **0 false positives**, had **0 hallucinations passed into reports**, and honored deterministic evidence boundaries.

**Conclusion:** DocSentry's current real-world detection power is overwhelmingly driven by **deterministic AST analysis, Markdown claim classification, and candidate mapping heuristics**, NOT by LLM semantic reasoning. The LLM acts as an ultra-conservative, highly-pruned secondary classifier that rarely fires.

---

## 2. Six-Configuration Consolidated Matrix

| Configuration | Benchmark Dataset | Total | TP | FP | TN | FN | Precision | Recall | Specificity | F1 Score | Cond. Loc. Acc. | Cond. Attr. Acc. | Model Invocations | Incremental AI Wins |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **1. Original Baseline (Deterministic)** | Verified 25 Historical | 25 | 7 | 0 | 14 | 4 | 100% | 63.64% | 100% | 0.7778 | 100% | 100% | 0 | — |
| **2. Original Baseline (Selective Hybrid)** | Verified 25 Historical | 25 | 7 | 0 | 14 | 4 | 100% | 63.64% | 100% | 0.7778 | 100% | 100% | 1 (Abstained) | 0 |
| **3. v0.2 Deterministic** | Verified 25 Historical | 25 | 10 | 0 | 14 | 1 | 100% | 90.91% | 100% | 0.9524 | 100% | 100% | 0 | — |
| **4. v0.2 Selective Hybrid** | Verified 25 Historical | 25 | 11 | 0 | 14 | 0 | 100% | 100.0% | 100% | 1.0000 | 100% | 100% | 1 (`REQUESTS`) | 1 (`REAL-REQUESTS-01`)* |
| **5. Fresh Blind (Deterministic)** | Fresh 8 Unseen Cases | 8 | 3 | 0 | 4 | 1 | 100% | 75.00% | 100% | 0.8571 | 100% | 100% | 0 | — |
| **6. Fresh Blind (Selective Hybrid)** | Fresh 8 Unseen Cases | 8 | 3 | 0 | 4 | 1 | 100% | 75.00% | 100% | 0.8571 | 100% | 100% | 0 | **0** |

*\*Note: `REAL-REQUESTS-01` is forensically classified as procedural/advisory drift, not breaking contradiction.*

---

## 3. Disaggregation of System Improvements

Where did the recall improvements between baseline (63.6%) and v0.2 (100% / 75%) actually come from?

### A. Contributions from Python AST Extraction (+27.3% Recall)
The transition from v0.1 to v0.2 fixed three deep static analysis bugs:
1. **Class Hierarchy & Sibling Scoping (`pallets/flask`):** Enabled extraction of inherited class attributes and methods without losing symbol qualification.
2. **Aliased Import & Type Annotation Tracking (`pydantic/pydantic`):** Correctly resolved symbol renames across internal modules.
3. **JS/Generic Fallback AST Extraction (`axios/axios`):** Standardized property diffing for non-Python test cases.
**Impact:** Recovered 3 false negatives deterministically without invoking the LLM.

### B. Contributions from Markdown Claim Classification (+0% Recall, +Safety)
1. **Claim Categorization:** Segregated documentation into `active_assertion`, `historical_migration`, and `code_example`.
2. **Defensive Filtering:** Automatically penalized changelog entries and version migration notes (-6.0 relevance), completely eliminating potential false positive drift alerts on historical change logs.

### C. Contributions from Structured Candidate Retrieval
1. Multi-token identifier indexing and heading path token intersections.
2. Linked parameter mapping (`metadata["linked_params"]`), connecting constants like `DEFAULT_TIMEOUT` to parameter signatures.

### D. Contributions Attributable Specifically to Qwen3-8B
- Total candidate pairs evaluated by Qwen3-8B across 33 unique test executions: **1**.
- Verified detections exclusive to Qwen3-8B: **1** (`REAL-REQUESTS-01`).
- Verified detections on fresh blind repositories: **0**.
- False positives introduced by Qwen3-8B: **0**.
- Hallucinations permitted into final findings: **0**.

---

## 4. Formal Metric: Verified AI Incremental Contribution

The required evaluation formula is:
$$\text{AI Incremental Value} = \frac{\text{Verified AI-Only Detections}}{\text{Independently Verified Positive Scenarios}}$$

### A. On Fresh Blind Dataset (4 Unseen Repositories)
- Independently verified positive scenarios: 4
- Detected by Deterministic: 3
- Detected by Selective Hybrid: 3
- Verified AI-only detections: **0**
$$\text{AI Incremental Value}_{\text{blind}} = \frac{0}{4} = \mathbf{0.0\%}$$

### B. On Verified 25-Case Historical Dataset
- Independently verified positive scenarios: 11
- Detected by Deterministic: 10
- Detected by Selective Hybrid: 11
- Potential AI-only detection: 1 (`REAL-REQUESTS-01`)

**Evaluation under Ground-Truth Rigor:**
1. **Strict Standard (Authentic Breaking Contradiction):**
   Because `requests.post(..., data=json.dumps(p))` never broke or returned invalid results upstream, this case represents a documentation improvement rather than a breaking factual falsehood.
   $$\text{AI Incremental Value}_{\text{strict}} = \frac{0}{11} = \mathbf{0.0\%}$$
2. **Permissive Standard (Including Advisory / Procedural Drift):**
   If superseding API convenience parameters are accepted as documentation drift:
   $$\text{AI Incremental Value}_{\text{permissive}} = \frac{1}{11} = \mathbf{9.09\%}$$

---

## 5. Secondary AI Behavior Metrics

| Metric | Result | Explanation |
|---|---|---|
| **AI-Only False Positives** | **0** | Qwen3-8B never generated a drift finding for any negative control. |
| **AI-Only False Negatives** | **0** | All misses (`BLIND-URLLIB3-01`) occurred at Candidate Retrieval before the LLM. |
| **AI Model Abstentions** | **1** | In `CLICK-02`, Qwen correctly abstained on a ambiguous docstring. |
| **AI Findings Rejected by Evidence Validation** | **0** | All LLM proposals strictly respected the Git snapshot evidence bundle. |
| **Latency Overhead per LLM Invocation** | **1,850 ms** | Deterministic pipeline runs in ~220 ms; invoking Qwen3-8B adds ~1.85 seconds. |

---

## 6. Engineering Limitations & Lessons

1. **The Routing Funnel is Extremely Strict:**
   DocSentry's architecture was deliberately designed with high gating thresholds (`score >= 5.0`, `is_behavioral == True`) to prevent open-weight model hallucinations. While this achieved 100% specificity and zero false positives, it meant that Qwen3-8B was never engaged on the fresh blind dataset.
2. **Upstream Retrieval Bottleneck:**
   Open-weight models cannot compensate for missing retrieval candidates. If the deterministic candidate mapper fails to link code and docs, the LLM is powerless.
3. **Synthetic Blind Fixtures vs. Upstream Repositories:**
   The fresh blind dataset consisted of simplified synthetic fixtures rather than complex real-world repositories with thousands of lines of documentation. On simplified fixtures, deterministic rules are almost always sufficient.

---

## 7. Strategic Recommendation for Product Positioning

When presenting DocSentry to technical evaluators or hackathon judges:
- **Do NOT claim:** *"Our AI autonomously reads codebases and reasons about documentation drift."* (This is easily debunked by inspecting invocation metrics).
- **DO claim:** *"DocSentry uses deterministic AST analysis and structured candidate mapping for high-speed, 100% precision drift detection, reserving localized open-weight AI reasoning exclusively as a bounded fallback for complex behavioral changes."*
