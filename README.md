<div align="center">

# DocSentry
### *Your code evolves. Your documentation should keep up.*

[![CI](https://github.com/Atharv386/DocSentary/actions/workflows/ci.yml/badge.svg)](https://github.com/Atharv386/DocSentary/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://python.org)
[![PR Analysis](https://img.shields.io/badge/GitHub%20Actions-PR%20Drift%20Detector-green.svg)](.github/workflows/docsentry.yml)

**Catch documentation drift in pull requests before it reaches production.**

[Overview](#-the-problem) • [How It Works](#-how-it-works) • [Supported Checks](#-supported-checks) • [CLI Quickstart](#-cli-quickstart) • [GitHub Actions](#-github-actions-workflow) • [Architecture](#-architecture) • [Evaluation](#-evaluation--historical-replay)

</div>

---

## 🔍 The Problem

Documentation silently becomes incorrect as software evolves.

A developer updates a parameter's default value (`timeout: int = 30` ➔ `60`), removes an obsolete argument, renames a CLI flag, or modifies configuration keys. The code gets merged, but the documentation is left unchanged. The result is documentation that looks trustworthy but actively misleads developers.

Standard linters only verify markdown formatting and broken links. **DocSentry proves whether your documentation statements are still true after a code change.**

---

## 🛡️ The DocSentry Guarantee: Zero-Hallucination Evidence

Every single drift finding detected by DocSentry provides an immutable, verifiable link between the code change and the outdated sentence:

```
[OUTDATED DOCUMENTATION]                                [ACTUAL CODE CHANGE]
docs/config.md:23                                       src/client.py:12
-------------------------------------------------       -------------------------------------------------
"The default timeout is 30 seconds."               ➔    def connect(..., timeout=60): ...
```

- **Trust before intelligence:** Every finding must cite the exact documentation file, line span, code file, symbol, and diff evidence.
- **Deterministic-first:** Numerical defaults, signatures, CLI flags, and constants are verified using Python AST and Markdown source maps.
- **Bounded semantic verifier:** Open-weight model inference is strictly bounded to candidate evidence packs. Hallucinated lines or quotes are systematically rejected by our evidence validation trust boundary.

---

## ⚡ Supported Checks

| Rule ID | Category | Detection Condition | Default Status |
| :--- | :--- | :--- | :--- |
| `PY-DEFAULT-001` | **Stale Default** | Parameter default changed in AST, but docs still bind the old literal | `DRIFT` |
| `PY-PARAM-002` | **Stale Parameter** | Parameter removed or renamed, but docs still reference it | `DRIFT` / `POTENTIAL_DRIFT` |
| `PY-SYMBOL-003` | **Removed Symbol** | Function/class removed, but docs still instruct users to invoke it | `POTENTIAL_DRIFT` |
| `PY-CONFIG-004` | **Stale Flag / Key** | CLI flag or config key modified, docs table retains old flag | `DRIFT` |
| `PY-CONST-005` | **Stale Constant** | Literal constant value updated, docs retain old value | `DRIFT` |
| `PY-BEHAVIOR-006` | **Behavioral Drift** | Semantic prose change analyzed via bounded open-weight model | `POTENTIAL_DRIFT` |
| `PY-RETURN-007` | **Return Contract Drift** | Return type, tuple shape, or generator change invalidating docs | `POTENTIAL_DRIFT` |

---

## 🚀 CLI Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/Atharv386/DocSentary.git
cd DocSentary

# Create virtual environment & install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Analyze a Pull Request / Local Commits

```bash
# Scan between base commit and head commit
docsentry scan --repo . --base <BASE_SHA> --head <HEAD_SHA> --output-dir .docsentry

# Run deterministic checks only (no API key needed)
docsentry scan --repo . --base <BASE_SHA> --head <HEAD_SHA> --no-model

# Validate a generated ScanReport JSON artifact
docsentry validate-report .docsentry/report.json

# Execute the comprehensive 50-scenario evaluation benchmark suite
docsentry evaluate --no-model

# Execute the 50-scenario benchmark with local Qwen3-8B (Ollama)
docsentry evaluate

# Run the real-world HTTPX PR #653 evaluation case study
python examples/real-world-evaluation/reproduce.py

# Execute the historical replay evaluation suite
docsentry replay --manifest examples/history/replay.json
```

---

## 🔬 Technical Benchmarks & Empirical Validation

DocSentry maintains a rigorous, reproducible evaluation protocol that strictly separates **authentic upstream open-source history** from **synthetic stress fixtures**.

All benchmarks were independently validated on an **Apple Silicon MacBook Pro M4 (16GB Unified Memory)** using local open-weight inference with **`qwen3:8b` via Ollama**.

---

### 1. Authentic Open-Source Benchmark (68 Cases across 15 Repositories)

Evaluated across authentic historical pull requests and Git snapshots from 15 major open-source ecosystems: `psf/requests`, `urllib3/urllib3`, `marshmallow-code/marshmallow`, `pallets/werkzeug`, `tornadoweb/tornado`, `redis/redis-py`, `psutil/psutil`, `encode/httpx`, `encode/starlette`, `pallets/flask`, `pallets/click`, `pydantic/pydantic`, `axios/axios`, `facebook/react`, and `fastapi/fastapi`.

| Metric | Deterministic (Static AST) | Selective Hybrid (DocSentry Core) | AI Incremental Lift |
| :--- | :---: | :---: | :---: |
| **Total Authentic Cases** | 68 | **68** | — |
| **Positive Drift Scenarios** | 38 | **38** | — |
| **Negative Controls** | 30 | **30** | — |
| **True Positives (TP)** | 24 | **30** | **+6 Verified AI Wins** |
| **False Positives (FP)** | **0** | **0** | **0.0% (Zero False Alarms)** |
| **True Negatives (TN)** | **30** | **30** | **100.0% Specificity** |
| **False Negatives (FN)** | 14 | **8** | -42.9% Missed Drift Reduction |
| **Precision (PPV)** | **100.0%** | **100.0%** | **Invariant Preserved** |
| **Recall (Sensitivity)** | 63.16% | **78.95%** | **+15.79% Absolute Lift** |
| **Specificity (TNR)** | **100.0%** | **100.0%** | **100.0% Clean Controls** |
| **F1 Score** | 0.7742 | **0.8824** | **+0.1082 F1 Improvement** |
| **Average Scan Latency** | **234.5 ms** | **2,140.2 ms** | 94.1% faster than naive LLM |
| **LLM Invocation Rate** | 0.0% | **11.76% (8 calls / 68 cases)** | Strictly bounded selective gating |

#### The 6 Verified Incremental AI Wins
In all 6 cases, function signatures never changed; drift occurred purely in the behavioral, return, or exception contracts that static AST analyzers are structurally blind to:
1. **`REAL-REQUESTS-01` (`psf/requests`):** Event hook response mutation contract drift.
2. **`REAL-URLLIB3-02` (`urllib3/urllib3`):** `HTTPConnection.connect()` timeout propagation contract drift.
3. **`REAL-URLLIB3-03` (`urllib3/urllib3`):** SSL context exception handling recommendation invalidation.
4. **`REAL-MARSHMALLOW-01` (`marshmallow-code/marshmallow`):** `Schema.dump()` return tuple-unpacking contract break (`(data, errors)` ➔ `data`).
5. **`HELD-TORNADO-03` (`tornadoweb/tornado`):** `tornado.escape.to_unicode` type-enforcement exception contract drift.
6. **`HELD-REDIS-03` (`redis/redis-py`):** `Pipeline.execute()` error-handling contract change (`raise_on_error=True`).

---

### 2. Fresh Held-Out Generalization Evaluation (20 Cases across 4 Unseen Repositories)

To guarantee that DocSentry generalizes to new software ecosystems without overfitting, Phase 4 evaluated 20 authentic cases across four codebases never before tested during development:

| Repository | Domain | Cases | Positive Drift | Negative Controls | Deterministic F1 | Selective Hybrid F1 | AI Wins |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `pallets/werkzeug` | WSGI Web Engine | 5 | 3 | 2 | 0.8000 | **0.8000** | 0 |
| `tornadoweb/tornado` | Async Networking | 5 | 3 | 2 | 0.8000 | **1.0000** | **1** (`HELD-TORNADO-03`) |
| `redis/redis-py` | Datastore Client | 5 | 3 | 2 | 0.8000 | **1.0000** | **1** (`HELD-REDIS-03`) |
| `psutil/psutil` | OS / Systems | 5 | 3 | 2 | 0.8000 | **0.8000** | 0 |
| **Held-Out Total** | | **20** | **12** | **8** | **0.8000** | **0.9091** | **2 Verified Wins** |

- **Held-Out Precision:** **100.0%** (0 false positives across all 8 negative controls).
- **Held-Out Recall:** **83.33%** (10 / 12 positive cases detected).
- **Held-Out F1 Score:** **0.9091** (+0.1091 lift over deterministic).

---

### 3. Adversarial Semantic Stress Suite (10 Targeted Scenarios)

Evaluates extreme edge cases probing semantic understanding vs deterministic pattern matching:
- **100.0% Specificity on Negative Traps:**
  - *Homonym Trap (`ADV-02`):* `SessionMixin.max_age` (user session timeout) vs HTTP `Cache-Control: max-age=3600`. Correctly disambiguated via scoped candidate mapping.
  - *Internal Invariant Refactor (`ADV-03`):* Regex parser rewritten as DFA state machine. Public contract preserved; no false alarms.
  - *Backward-Compatible Addition (`ADV-04`):* Added `timeout=None` kwarg; docs explaining base `client.get(url)` remain valid.
  - *Intentional Historical Note (`ADV-10`):* Deprecated helper documented in `history.md` under *"In version 1.x..."*. Filtered out by typed Markdown claim classification (`historical_migration`).
- **Semantic Reasoning Victories:** Caught breaking behavioral mutations without signature changes (`ADV-06`) and iterator return type invalidation (`ADV-07`).

---

### 4. Seven-Configuration Architectural Ablation

| Configuration | TP | FP | TN | FN | Precision | Recall | F1 Score | Verified AI Wins |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1. v0.3 Deterministic Baseline (48 cases) | 16 | 0 | 22 | 10 | 100.0% | 61.54% | 0.7619 | 0 |
| 2. v0.3 Selective Hybrid Baseline (48 cases) | 20 | 0 | 22 | 6 | 100.0% | 76.92% | 0.8696 | 4 |
| 3. v0.4 Improved Deterministic (68 cases) | 24 | 0 | 30 | 14 | 100.0% | 63.16% | 0.7742 | 0 |
| **4. v0.4 Improved Selective Hybrid (68 cases)** | **30** | **0** | **30** | **8** | **100.0%** | **78.95%** | **0.8824** | **6** |
| 5. Hybrid w/o Claim Classification | 30 | 2 | 28 | 8 | 93.75% | 78.95% | 0.8571 | 6 |
| 6. Hybrid w/o Relationship-Aware Retrieval | 24 | 1 | 29 | 14 | 96.00% | 63.16% | 0.7619 | 0 |
| 7. Hybrid w/o Qwen Reasoning (Pure AST) | 24 | 0 | 30 | 14 | 100.0% | 63.16% | 0.7742 | 0 |

**Key Ablation Insights:**
1. **Qwen3-8B Semantic Verifier:** Delivers $+15.79\%$ recall lift and $+0.1082$ F1 score with zero false positives.
2. **Markdown Claim Classification:** Structural prerequisite for 100% precision; prevents 2 false positives on legacy migration documentation.
3. **Relationship-Aware Retrieval:** Eliminates homonym false positives and bridges the AST-to-prose gap necessary for all 6 AI wins.
4. **Efficiency:** Selective gating calls the LLM on only 11.76% of candidates, reducing latency by **94.1%** compared to naive all-pairs verification.

---

### 5. Cross-Repository & Dual-Snapshot Evidence Guarantees

DocSentry natively supports decoupled documentation setups (e.g. `facebook/react` source vs `reactjs/react.dev` docs site):
- **Flags:** `--docs-repo <path>`, `--docs-ref <sha_or_branch>`, `--docs-mapping <json_file>`.
- **Fail-Safe Abstention Protocol:** If a docs repository is provided but the revision mapping cannot be verified against the code commit, DocSentry **immediately abstains** to avoid noisy false alarms on release branches.
- **Dual-Snapshot Verification:** Every finding is validated against exact lines in immutable Git snapshots at both code HEAD and docs HEAD. The LLM can never manufacture evidence.

---

---

## 🤖 GitHub Actions Workflow

Integrate DocSentry directly into your CI pipeline using `.github/workflows/docsentry.yml`:

```yaml
name: DocSentry PR Analysis
on:
  pull_request:
    types: [opened, synchronize, reopened]

permissions:
  contents: read

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install DocSentry
        run: pip install -e .

      - name: Run scan
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
          HEAD_SHA: ${{ github.event.pull_request.head.sha }}
          DOCSENTRY_MODEL_API_KEY: ${{ secrets.DOCSENTRY_MODEL_API_KEY || secrets.DOCGUARD_MODEL_API_KEY }}
        run: |
          docsentry scan --repo . --base "$BASE_SHA" --head "$HEAD_SHA" \
            --output-dir artifacts/docsentry

      - name: Publish Step Summary
        if: always()
        run: |
          if [ -f artifacts/docsentry/report.md ]; then
            cat artifacts/docsentry/report.md >> "$GITHUB_STEP_SUMMARY"
          fi
```

---

## 🏗️ Architecture

```
GitHub PR / CLI (base_sha, head_sha)
         │
         ▼
    ScanContext ───► Git Runner (merge-base, diff, snapshots)
         │                    │
         ├────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
  Python AST Facts     DocSpan Parser       Raw Diff Hunks
         │                    │                    │
         └────────────────────┼────────────────────┘
                              ▼
                     Candidate Mapper
                   (Weighted Relevance)
                              │
                              ▼
                  Deterministic Rule Engine
                 (PY-DEFAULT, PY-PARAM, etc.)
                              │
                              ▼
                 Bounded Model Verifier (AI)
                  (Open-Weight Protocol)
                              │
                              ▼
                  Evidence Validator Gate
                 (Zero Hallucination Proof)
                              │
                              ▼
                  ScanReport (JSON & Markdown)
```

---

## 📊 Evaluation & Historical Replay

DocSentry includes a validated evaluation dataset (`examples/history/replay.json`) containing 8 test scenarios:

1. **F-01 (stale-default)**: Default parameter change `30` ➔ `60` (`DRIFT`)
2. **F-02 (parameter-added)**: New parameter `retries` added (`POTENTIAL_DRIFT`)
3. **F-03 (removed-symbol)**: Function `old_login` removed (`POTENTIAL_DRIFT`)
4. **F-04 (renamed-flag)**: CLI flag `--timeout` ➔ `--request-timeout` (`DRIFT`)
5. **F-05 (no-doc-impact)**: Internal refactor with unchanged public interface (`NO FINDING`)
6. **F-06 (docs-fixed-same-pr)**: Simultaneous code and documentation update (`NO FINDING`)
7. **F-07 (ambiguous-runtime)**: Dynamic reflection (`UNCERTAIN`)
8. **F-08 (historical-fix)**: Historical evaluation of pre-fix commits (`DRIFT`)

Run the full replay evaluation with:
```bash
docsentry replay --manifest examples/history/replay.json
```

---

## ⚙️ Configuration (`docsentry.yml`)

```yaml
version: 1
scope:
  source_globs: ["**/*.py"]
  docs_globs: ["**/*.md", "**/*.mdx"]
  exclude_globs:
    - "**/.venv/**"
    - "**/build/**"
    - "**/dist/**"
limits:
  max_files: 250
  max_file_bytes: 500000
  max_doc_spans_per_fact: 5
model:
  enabled: true
  timeout_seconds: 30
report:
  include_no_drift: false
  include_uncertain: true
  fail_on: never
```

---

## ⚖️ License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
