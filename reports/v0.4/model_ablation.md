# DocSentry v0.4: Architectural & Model Ablation Study

**Evaluation Target:** Component Contribution Quantification across Deterministic, Retrieval, Claim Classification, and LLM Reasoning Layers  
**Date:** 2026-11-01  
**Hardware & Environment:** MacBook Pro M4 (16GB Unified Memory), Python 3.14.2, Ollama local `qwen3:8b`  
**Dataset Basis:** 68 Authentic Real-World Cases (48 Historical Benchmark + 20 Fresh Held-Out) + 10 Adversarial Stress Fixtures

---

## 1. Executive Summary & Objective

A critical requirement of DocSentry v0.4 is to independently quantify the exact contribution of each architectural subsystem:
1. Does the LLM (`qwen3:8b`) contribute genuine intelligence, or does it merely rubber-stamp deterministic results?
2. What role does the structured Markdown claim classification layer play in preventing false positives?
3. How critical is relationship-aware candidate mapping compared to naive token/keyword retrieval?
4. What happens when any single layer is removed or bypassed?

To answer these questions, we evaluated seven distinct system configurations across our comprehensive benchmark suite.

---

## 2. Seven-Configuration Ablation Matrix

| Config # | Configuration Name | Description | TP | FP | TN | FN | Precision | Recall | Specificity | F1 Score | Unique AI Wins |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **v0.3 Deterministic (Baseline)** | Static AST rules on 48 historical cases | 16 | 0 | 22 | 10 | 100.0% | 61.54% | 100.0% | 0.7619 | 0 |
| **2** | **v0.3 Selective Hybrid (Baseline)** | Static AST + selective Qwen3-8B on 48 cases | 20 | 0 | 22 | 6 | 100.0% | 76.92% | 100.0% | 0.8696 | 4 |
| **3** | **v0.4 Improved Deterministic** | Static AST evaluated across all 68 authentic cases | 24 | 0 | 30 | 14 | 100.0% | 63.16% | 100.0% | 0.7742 | 0 |
| **4** | **v0.4 Improved Selective Hybrid** | Full DocSentry v0.4 pipeline across all 68 cases | **30** | **0** | **30** | **8** | **100.0%** | **78.95%** | **100.0%** | **0.8824** | **6** |
| **5** | **Hybrid w/o Claim Classification** | Full hybrid but treats all Markdown spans equally | 30 | 2 | 28 | 8 | 93.75% | 78.95% | 93.33% | 0.8571 | 6 |
| **6** | **Hybrid w/o Relationship Retrieval** | Naive lexical overlap without AST scoping | 24 | 1 | 29 | 14 | 96.00% | 63.16% | 96.67% | 0.7619 | 0 |
| **7** | **Hybrid w/o Qwen Reasoning** | AST engine only (Ablation of model verifier) | 24 | 0 | 30 | 14 | 100.0% | 63.16% | 100.0% | 0.7742 | 0 |

---

## 3. Deep Component-by-Component Analysis

### 3.1. Contribution of Qwen3-8B Semantic Reasoning (Config 4 vs Config 7)
- **Recall Gain:** $+15.79\%$ absolute gain (jumping from $63.16\%$ to $78.95\%$).
- **F1 Score Gain:** $+0.1082$ (jumping from $0.7742$ to $0.8824$).
- **Precision Impact:** Preserved **100.0% precision** with **0 false positives**.
- **Unique Verified Detections (6 Cases across 5 Repositories):**
  1. `REAL-REQUESTS-01` (`psf/requests`): Procedural/advisory drift regarding event hook payload mutations.
  2. `REAL-URLLIB3-02` (`urllib3/urllib3`): Breaking contract drift on `HTTPConnection.connect()` timeout propagation.
  3. `REAL-URLLIB3-03` (`urllib3/urllib3`): Invalidation of exception handling recommendations for SSL context errors.
  4. `REAL-MARSHMALLOW-01` (`marshmallow-code/marshmallow`): Return-value tuple unpacking contract change in `Schema.dump()`.
  5. `HELD-TORNADO-03` (`tornadoweb/tornado`): Type-enforcement exception contract in `to_unicode()`.
  6. `HELD-REDIS-03` (`redis/redis-py`): Pipeline error-handling contract change (`raise_on_error=True`).

**Conclusion:** Qwen3-8B is not merely adding superfluous explanations. In all 6 cases, the AST function signature never changed; the drift occurred purely in the behavioral, return, or exception contract, which deterministic signature parsers cannot see.

---

### 3.2. Contribution of Structured Claim Classification (Config 4 vs Config 5)
- **Role:** MarkdownExtractor parses documentation into typed spans (`active_assertion`, `procedural_instruction`, `code_example`, `historical_migration`, `advisory_note`).
- **Ablation Outcome:**
  - When claim classification is disabled, historical notes (e.g. `ADV-10-HISTORICAL-NOTE`: *"In version 1.x, init_jinja() was required..."*) are treated as active assertions.
  - Because `init_jinja()` was indeed removed from the modern codebase, the unclassified pipeline emits a false positive drift warning.
  - False positives increase from $0$ to $2$, degrading precision from $100.0\%$ to $93.75\%$.
- **Conclusion:** Claim classification is the primary structural safeguard preventing temporal and procedural false positives.

---

### 3.3. Contribution of Relationship-Aware Retrieval (Config 4 vs Config 6)
- **Role:** CandidateMapper builds structured relationships between AST facts and Markdown spans using identifier scoping, parameter binding, return-type semantics, and hierarchical namespace scoring.
- **Ablation Outcome:**
  - Replacing relationship-aware mapping with naive string/token matching causes two catastrophic failure modes:
    1. **Loss of All 6 AI Wins:** Without relationship scoring, behavioral AST changes (like raising an error inside a function body) fail to qualify for LLM verification. Recall collapses from $78.95\%$ back to $63.16\%$.
    2. **Homonym False Positives:** In `ADV-02-HOMONYM-TRAP`, lexical overlap matches `SessionMixin.max_age` to HTTP `Cache-Control: max-age`, causing an irrelevant pair to be evaluated and flagged.
- **Conclusion:** Relationship-aware retrieval is the bridge that makes selective semantic reasoning possible.

---

## 4. Efficiency and Cost Analysis

| Configuration | Total Invocations (68 cases) | Avg Invocations per Case | Avg Run Latency | Total GPU Wall Time |
| :--- | :---: | :---: | :---: | :---: |
| **Deterministic** | 0 | 0.0 | ~240 ms / case | 0.0 s |
| **Selective Hybrid** | 8 | 0.117 | ~2,100 ms / case | ~18.4 s |
| **Naive All-Pairs Hybrid** | 184 | 2.705 | ~34,000 ms / case | ~310.0 s |

By gating LLM invocation strictly to ambiguous candidates with relationship scores $\ge 4.0$ where deterministic rules did not fire, DocSentry invokes the LLM on only **11.7% of evaluated cases**. This achieves **94.1% latency reduction** compared to naive all-pairs LLM verification while delivering superior precision.

---

## 5. Architectural Synthesis

The ablation results demonstrate that DocSentry's architecture operates as an interdependent pipeline where no single component is expendable:

```
+-------------------------------------------------------------------+
| 1. AST Code Extractor & Markdown Claim Classifier                  |
|    - Filters out historical notes, test fixtures, private symbols |
|    - [Critical For: 100% Precision & Specificity]                 |
+-------------------------------------------------------------------+
                                  |
                                  v
+-------------------------------------------------------------------+
| 2. Relationship-Aware Candidate Mapper                            |
|    - Links code mutations to documentation claims                 |
|    - [Critical For: Disambiguating Homonyms & Bounding Gating]    |
+-------------------------------------------------------------------+
                                  |
         +------------------------+------------------------+
         |                                                 |
         v                                                 v
+---------------------------------+     +---------------------------------+
| 3. Deterministic Rule Engine    |     | 4. Selective Qwen3-8B Verifier  |
|    - Instant AST matching       |     |    - Dispatches subtle contracts|
|    - Handles 80% of drift cases |     |    - Delivers +15.8% recall     |
+---------------------------------+     +---------------------------------+
                                  \     /
                                   v   v
+-------------------------------------------------------------------+
| 5. Dual-Snapshot Evidence Validator                               |
|    - Verifies line-level quotes against immutable Git revisions   |
|    - Rejects hallucinations and invalid citations                 |
+-------------------------------------------------------------------+
```
