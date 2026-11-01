# Forensic Ground-Truth Audit: Eight Blind Evaluation Scenarios

**Evaluation Scope:** All 8 Scenarios in the Fresh Blind Evaluation Dataset (`urllib3`, `marshmallow`, `aiohttp`, `starlette`)  
**Auditor:** Principal Evaluation Researcher & Quality Assurance Architect  
**Objective:** Independent verification of commit SHAs, code authenticity, documentation sentence reality, and ground truth validity  

---

## 1. Executive Summary & Critical Finding

DocSentry previously reported performance against an 8-scenario "fresh blind" benchmark dataset spanning four previously unseen repositories (`urllib3`, `marshmallow`, `aiohttp`, `starlette`).

This independent audit conducted a forensic verification of every scenario's claimed ground truth against upstream GitHub history.

### Critical Audit Finding: All 8 Scenarios are Synthetic Fixtures
- **None of the 8 blind scenarios represent authentic, cloned historical git snapshots from GitHub.**
- All 8 scenarios use **synthetic placeholder commit SHAs** (e.g. `c101010101010101010101010101010101010101` through `c108...`).
- The code and documentation files are minimal, isolated synthetic snippets (e.g., 2-line Python files and 1-line Markdown files) constructed to test specific drift types (constant change, parameter removal, default change, symbol removal, and negative control refactorings).
- While the scenarios are logically sound as **constructed synthetic integration tests**, they must be formally classified as **`QUESTIONABLE / CONSTRUCTED FIXTURES`** rather than authentic historical real-world PRs.

---

## 2. Complete Blind Scenario Ground-Truth Audit Table

| Scenario ID | Repository | Drift Type Claimed | Upstream Topic Reality | Commit SHA Status | Doc Sentence Reality | Ground-Truth Validity | Final Classification |
|:---|:---|:---|:---|:---:|:---:|:---:|:---:|
| `BLIND-URLLIB3-01` | `urllib3/urllib3` | `constant_value_change` | In urllib3 v1.x, timeout policy was refactored, but `DEFAULT_TIMEOUT` is `None` (or object). | Synthetic Mock (`c101...`) | Synthetic fixture sentence (`"Default pool timeout is set to 3.0 seconds."`). Never existed upstream. | Logically sound test case; synthetic text. | **QUESTIONABLE** (Constructed Fixture) |
| `BLIND-URLLIB3-NC1` | `urllib3/urllib3` | `negative_control_refactor` | Internal buffer optimization comment in `_get_conn()`. | Synthetic Mock (`c102...`) | Synthetic documentation span. | Logically sound negative control; synthetic text. | **QUESTIONABLE** (Constructed Fixture) |
| `BLIND-MARSHMALLOW-01` | `marshmallow-code/marshmallow` | `parameter_removed` | Marshmallow v3 genuinely deprecated/removed `missing` in favor of `load_default`. | Synthetic Mock (`c103...`) | Synthetic documentation span. | Authentic upstream architectural topic, but condensed into synthetic fixture. | **QUESTIONABLE** (Constructed Fixture) |
| `BLIND-MARSHMALLOW-NC1` | `marshmallow-code/marshmallow` | `negative_control_refactor` | Internal fast-path empty check in `validate()`. | Synthetic Mock (`c104...`) | Synthetic documentation span. | Logically sound negative control; synthetic text. | **QUESTIONABLE** (Constructed Fixture) |
| `BLIND-AIOHTTP-01` | `aio-libs/aiohttp` | `default_value_change` | AIOHTTP historically used 300s timeout in early versions, later refactored into `ClientTimeout`. | Synthetic Mock (`c105...`) | Synthetic documentation span. | Logically sound test case; synthetic text. | **QUESTIONABLE** (Constructed Fixture) |
| `BLIND-AIOHTTP-NC1` | `aio-libs/aiohttp` | `negative_control_refactor` | Route table initialization docstring comment in `web_app.py`. | Synthetic Mock (`c106...`) | Synthetic documentation span. | Logically sound negative control; synthetic text. | **QUESTIONABLE** (Constructed Fixture) |
| `BLIND-STARLETTE-01` | `encode/starlette` | `symbol_removed` | `BaseHTTPMiddleware` was criticized in discussions, but has NOT been removed from Starlette. | Synthetic Mock (`c107...`) | Synthetic documentation span. | Hypothetical breaking change; symbol was not removed in upstream. | **QUESTIONABLE** (Constructed Fixture) |
| `BLIND-STARLETTE-NC1` | `encode/starlette` | `negative_control_refactor` | Internal comment in `JSONResponse` class. | Synthetic Mock (`c108...`) | Synthetic documentation span. | Logically sound negative control; synthetic text. | **QUESTIONABLE** (Constructed Fixture) |

---

## 3. Detailed Forensic Analysis by Repository

### 3.1 `urllib3/urllib3` (`BLIND-URLLIB3-01` & `NC1`)
- **Code Snippet:** `DEFAULT_TIMEOUT = 3.0` $\rightarrow$ `DEFAULT_TIMEOUT = 5.0`
- **Doc Snippet:** `"Default pool timeout is set to 3.0 seconds."`
- **Forensic Upstream Reality:** In authentic `urllib3/urllib3`, timeout management is handled via the `urllib3.util.Timeout` class where `DEFAULT_TIMEOUT = _Default()` (a sentinel object) rather than a float literal. Furthermore, `docs/user-guide.rst` never contained the exact phrase `"Default pool timeout is set to 3.0 seconds."`
- **Verdict:** The scenario was manually constructed to test constant mutation detection.

### 3.2 `marshmallow-code/marshmallow` (`BLIND-MARSHMALLOW-01` & `NC1`)
- **Code Snippet:** Removal of `missing=None` parameter in `Field.__init__`.
- **Doc Snippet:** `"Provide a fallback value when deserializing using the missing argument."`
- **Forensic Upstream Reality:** Marshmallow version 3.0 did indeed execute a major breaking refactor where `missing` was renamed to `load_default` (and `default` was renamed to `dump_default`). However, the scenario does not clone the actual multi-thousand-line Marshmallow repository commit; it abstracts the change into an isolated 5-line fixture.
- **Verdict:** Valid architectural topic, but implemented as an isolated synthetic fixture.

### 3.3 `aio-libs/aiohttp` (`BLIND-AIOHTTP-01` & `NC1`)
- **Code Snippet:** `ClientSession.__init__(timeout: int = 300)` $\rightarrow$ `60`.
- **Doc Snippet:** `"Session connection timeout defaults to 300 seconds."`
- **Forensic Upstream Reality:** In authentic `aiohttp`, `ClientSession` accepts a `ClientTimeout` object defaulting to `aiohttp.helpers.sentinel` or `ClientTimeout(total=5*60)`. It does not accept a raw integer literal `timeout: int = 300`.
- **Verdict:** Synthetic default change fixture.

### 3.4 `encode/starlette` (`BLIND-STARLETTE-01` & `NC1`)
- **Code Snippet:** Complete removal of `BaseHTTPMiddleware` from `starlette/middleware/base.py`.
- **Doc Snippet:** `"Wrap ASGI apps with BaseHTTPMiddleware to process streaming requests."`
- **Forensic Upstream Reality:** In real-world Starlette, `BaseHTTPMiddleware` has never been removed. While maintainers have documented its limitations regarding streaming responses, it remains present in Starlette v0.38+.
- **Verdict:** Hypothetical symbol deletion scenario.

---

## 4. Impact on Benchmark Metrics

Because all 8 scenarios are synthetic approximations, reporting them as an authentic "blind evaluation of real-world open-source repositories" is scientifically inaccurate.

### Transparent Denominator Disclosure:
- **Authentic Historical Real-World Scenarios in Blind Set:** **0 / 8**
- **Logically Sound Synthetic Integration Test Cases:** **8 / 8**
  - Syntactic Positive Cases: 4 (1 constant, 1 parameter, 1 default, 1 symbol)
  - Negative Control Cases: 4 (internal refactoring / comments)
- **Verified Real-World Generalization Claim:** **UNPROVEN**. DocSentry has proven that its rules detect synthetic fixtures of these types, but true real-world generalisation to uncurated repositories requires a fully authentic, multi-file historical benchmark dataset.
