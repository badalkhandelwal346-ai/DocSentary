# DocSentry v0.4: Adversarial Semantic Benchmark Report

## 1. Executive Summary & Objective

In Phase 3 of DocSentry v0.4, we designed and executed an **Adversarial Semantic Benchmark** composed of 10 targeted evaluation scenarios. The objective of this benchmark is to rigorously probe the boundary between deterministic pattern matching and semantic reasoning, specifically investigating:
- **Vocabulary Discrepancies:** Can DocSentry detect drift when documentation uses prose terminology that differs entirely from code identifiers?
- **Homonym & False Match Traps:** Does DocSentry avoid false positives when code identifiers and documentation terms share the exact same name but operate in completely different semantic domains?
- **Contractual & Invariant Integrity:** Can DocSentry distinguish internal refactoring from external contractual breaks?
- **Backward Compatibility:** Can DocSentry verify that adding optional parameters or non-breaking features does not invalidate existing documentation?
- **Temporal & Historical Context:** Can DocSentry distinguish between an intentional historical note describing legacy behaviour and active documentation drift?

All 10 scenarios were independently executed on the frozen DocSentry engine with local `qwen3:8b` via Ollama.

---

## 2. Benchmark Architecture & Fixture Taxonomy

In accordance with strict evaluation protocols, synthetic and stress-testing fixtures are kept separate from authentic upstream benchmark datasets (`eval_corpus.json`).

| ID | Category | Code Change Summary | Documentation Claim | Expected Ground Truth |
| :--- | :--- | :--- | :--- | :--- |
| `ADV-01-VOCAB-GAP` | Vocabulary Gap | `DEFAULT_CONNECT_TIMEOUT = 10` → `5` | "The socket establishment limit is 10 seconds." | **Positive Drift** (Missed at retrieval) |
| `ADV-02-HOMONYM-TRAP` | Homonym Trap | `SessionMixin.max_age` changed from `int` to `timedelta` | "HTTP Cache-Control: max-age is set to 3600 seconds." | **Negative Control** (Preserved 100% Specificity) |
| `ADV-03-INTERNAL-INVARIANT` | Internal Refactor | `parse_url` regex replaced with state machine; return value contract unchanged | "parse_url decomposes URLs into a 6-tuple." | **Negative Control** (Preserved 100% Specificity) |
| `ADV-04-BACKWARD-COMPAT-ADD` | Backward-Compatible Addition | Added `timeout: float = 30.0` optional parameter to `client.get()` | "Call client.get(url, params=None) to query endpoints." | **Negative Control** (Preserved 100% Specificity) |
| `ADV-05-PROCEDURAL-OBSOLETE` | Procedural Incompleteness | Added native `auth_token` kwarg to client | "Users must manually construct an 'Authorization: Bearer' header." | **Positive Drift** (Missed at retrieval) |
| `ADV-06-BEHAVIORAL-NO-SIG` | Behavioral Change (No Sig) | `process(items)` now raises `ValueError` if `items` is empty (previously returned `[]`) | "If items is empty, process() returns an empty list." | **Positive Drift** (Detected by Qwen3-8B) |
| `ADV-07-RETURN-TYPE-ITERATOR` | Return Type Invalidation | `get_records()` changed from returning `list` to `Iterator` via `yield` | Example: `records = get_records(); records.sort()` | **Positive Drift** (Detected by Qwen3-8B) |
| `ADV-08-CALLGRAPH-DEFAULT` | Multi-Module Call Graph | `DEFAULT_PORT = 8080` → `9000` in `config.py`, imported into `server.py` | "Server listens on port 8080 by default." | **Positive Drift** (Missed at retrieval) |
| `ADV-09-SECURITY-INDIRECT` | Indirect Security Change | `cert_reqs='CERT_REQUIRED'` strictly enforced; disables permissive fallback | "By default, self-signed and untrusted certificates are permitted." | **Positive Drift** (Missed at retrieval) |
| `ADV-10-HISTORICAL-NOTE` | Intentional Historical Note | `init_jinja()` helper removed from current codebase | "In version 1.x, init_jinja() was required before rendering." | **Negative Control** (Preserved 100% Specificity) |

---

## 3. Empirical Results & Performance Matrix

The complete test execution was captured in `reports/v0.4/adversarial_results.json`:

```
Total Scenarios:         10
Positive Drift Cases:     6
Negative Controls:        4

True Positives (TP):      2  (ADV-06, ADV-07)
False Positives (FP):     0  (Zero false alarms across all negative controls)
True Negatives (TN):      4  (ADV-02, ADV-03, ADV-04, ADV-10)
False Negatives (FN):     4  (ADV-01, ADV-05, ADV-08, ADV-09)

Precision:             100.0%  (2 / 2)
Specificity:           100.0%  (4 / 4)
Positive Recall:        33.3%  (2 / 6)
Overall Accuracy:       60.0%  (6 / 10)
```

---

## 4. Deep-Dive Case Analysis

### 4.1. Semantic AI Successes (True Positives)

#### `ADV-06-BEHAVIORAL-NO-SIG` (Behavioral Contract Drift)
- **Code Context:** Function signature `def process(items):` remained completely identical. Inside the body, `if not items: return []` was altered to `if not items: raise ValueError("items must not be empty")`.
- **Doc Context:** "If items is empty, process() returns an empty list."
- **Execution Trace:**
  - Candidate Retrieval correctly flagged the entity `process` and matched the prose claim (score: 5.0).
  - Deterministic signature rules (`PY-SIG-001`, `PY-PARAM-002`) observed zero signature differences and yielded no finding.
  - Semantic Rule `PY-BEHAVIOR-006` dispatched the candidate pair and AST diff to `qwen3:8b`.
  - Qwen3-8B diagnosed the direct contradiction:
    > *"The code previously returned an empty list when items was falsy, but now raises a ValueError. The documentation claims it returns an empty list, which is no longer true."*
  - **Verdict:** True Positive verified.

#### `ADV-07-RETURN-TYPE-ITERATOR` (Contract & Example Drift)
- **Code Context:** `def get_records():` changed from accumulating results into `res = []; return res` to yielding elements with `yield record`.
- **Doc Context:** Code snippet in Markdown:
  ```python
  records = get_records()
  records.sort()  # Relies on list in-place mutation
  ```
- **Execution Trace:**
  - Claim Classifier parsed the snippet as a procedural contract assumption.
  - Candidate retrieval mapped `get_records` in code to the documentation code block.
  - Qwen3-8B evaluated whether the yielded generator satisfies `.sort()`:
    > *"get_records() now returns a generator object which does not have a .sort() method. Calling .sort() on the returned iterator will raise an AttributeError."*
  - **Verdict:** True Positive verified.

---

### 4.2. Precision & Specificity Wins (True Negatives)

#### `ADV-02-HOMONYM-TRAP` (Scope Disambiguation)
- **Trap:** A class `SessionMixin` in `auth/session.py` renamed its field `max_age: int` to `max_age: timedelta`. The documentation file `docs/caching.md` stated: `"HTTP Cache-Control: max-age is set to 3600 seconds."`
- **Defense Mechanism:** DocSentry's scoped candidate retrieval verified that `auth/session.py` is in an unrelated module from HTTP caching headers and verified that the doc claim was tagged as an HTTP configuration directive, not a Python class attribute. Candidate score remained below threshold.
- **Verdict:** True Negative. Zero false alarms.

#### `ADV-03-INTERNAL-INVARIANT` (Refactoring Invariance)
- **Trap:** The implementation of URL parsing was rewritten from a legacy regular expression to an explicit deterministic finite automaton (DFA). The public function signature and return tuple remained identical. The documentation stated: `"parse_url decomposes URLs into a 6-tuple."`
- **Defense Mechanism:** The semantic diff engine verified that the public return interface and tuple structure remained identical. Qwen3-8B was not triggered on internal AST implementation details.
- **Verdict:** True Negative. No false alarm.

#### `ADV-04-BACKWARD-COMPAT-ADD` (Additive Non-Breaking Changes)
- **Trap:** `client.get(url, params=None)` was extended with an optional keyword argument: `def get(url, params=None, timeout: float = 30.0):`. The existing documentation described basic usage: `"Call client.get(url, params=None) to query endpoints."`
- **Defense Mechanism:** DocSentry's signature drift rule distinguishes between breaking signature changes (removing parameters, reordering positional arguments, changing required parameters) and backward-compatible default additions. Because all existing call signatures remain valid, no drift was raised.
- **Verdict:** True Negative.

#### `ADV-10-HISTORICAL-NOTE` (Temporal & Migration Filtering)
- **Trap:** `init_jinja()` was completely removed from the codebase. In `docs/history.md`, the documentation read: `"In version 1.x, init_jinja() was required before template rendering."`
- **Defense Mechanism:** The claim classification layer classified the sentence with `claim_type: historical_migration` based on temporal markers ("In version 1.x", "was required"). Historical claims are excluded from active code drift checks.
- **Verdict:** True Negative.

---

### 4.3. Failure Analysis: The Candidate Retrieval Boundary (False Negatives)

Four scenarios (`ADV-01`, `ADV-05`, `ADV-08`, `ADV-09`) failed to detect drift. A forensic breakdown reveals an identical root cause across all four:

```
ADV-01 (Vocabulary Gap):           Candidate Score = 1.0  (Threshold: 4.0) -> LLM Not Invoked
ADV-05 (Procedural Obsolete):      Candidate Score = 3.0  (Threshold: 4.0) -> LLM Not Invoked
ADV-08 (Call Graph Default):       Candidate Score = 0.0  (Scoping Boundary) -> LLM Not Invoked
ADV-09 (Indirect Security):        Candidate Score = 2.0  (Threshold: 4.0) -> LLM Not Invoked
```

1. **Vocabulary Gap (`ADV-01` & `ADV-09`):**
   When code uses `DEFAULT_CONNECT_TIMEOUT` and documentation uses `"socket establishment limit"`, or code uses `cert_reqs='CERT_REQUIRED'` and doc uses `"untrusted SSL certificates"`, the Jaccard, token overlap, and AST identifier matching produce low similarity scores (< 3.0). Because DocSentry enforces a strict gating threshold (`min_score=4.0`) to avoid flooding the LLM and causing hallucinated false positives, Qwen3-8B was never invoked.
2. **Procedural Incompleteness (`ADV-05`):**
   Adding a convenient `auth_token` argument does not strictly break manual header passing (it still functions, but is now suboptimal/obsolete). Because the documentation statement `"Users must manually construct..."` did not reference `auth_token`, retrieval score was 3.0.
3. **Cross-Module Propagation (`ADV-08`):**
   DocSentry currently maps documentation to code files based on module naming and symbol references. When a constant in `config.py` is imported into `server.py` and documented in `server.md`, single-file scoping misses the cross-file dependency.

---

## 5. Architectural Implications & Recommendations

1. **Preserve the Precision Invariant:**
   DocSentry achieved **100% precision and 100% specificity** on the adversarial benchmark. It did not generate a single false positive on homonyms, refactorings, additive changes, or historical notes. This is a critical quality property that must never be compromised.
2. **Semantic Candidate Retrieval:**
   The failure mode is entirely localized to the retrieval stage. The LLM cannot reason over candidates it is never given. Rather than lowering deterministic thresholds (which would degrade precision), future iterations should introduce an intermediate semantic retrieval stage (e.g. lightweight embedding similarity or conceptual synonym expansion) specifically for behavioral drift candidates.
3. **Multi-File Symbol Resolution:**
   Cross-file imports (such as `config.py` constants re-exported or consumed in `server.py`) require call-graph propagation in the static analysis front-end.
