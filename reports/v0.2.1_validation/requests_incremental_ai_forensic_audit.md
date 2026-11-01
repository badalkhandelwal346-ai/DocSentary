# Forensic Ground-Truth Audit: `REAL-REQUESTS-01` (`psf/requests`)

**Scenario ID:** `REAL-REQUESTS-01`  
**Repository:** `psf/requests`  
**Referenced Upstream PR:** PR #2258 / #2464 (Native `json` parameter addition)  
**Evaluator:** Principal AI Evaluation Researcher & Systems Architect  
**Evaluation Scope:** Forensic verification of claimed incremental AI contribution  

---

## 1. Executive Summary & Objective

In DocSentry's evaluation reports, `REAL-REQUESTS-01` is cited as the primary real-world proof of incremental AI contribution: a scenario where deterministic static analysis produced 0 findings, but local `qwen3:8b` successfully diagnosed documentation drift.

The objective of this forensic audit is to independently verify every aspect of this claim against actual upstream repository history:
1. Did the code change authentically introduce native JSON support?
2. What behavior did the new parameter provide?
3. Does the documentation sentence explicitly require manual serialization, or merely describe one supported method?
4. Was the sentence accurate before the code change?
5. Did it become factually incorrect after the code change?
6. Is there an authentic contradiction, or only an additional capability?

---

## 2. Upstream Repository and Historical Investigation

### 2.1 The Code Change
In upstream `psf/requests` (released in version 2.4.2 via PR #2258 and PR #2464):
```python
# Upstream requests/api.py
def post(url, data=None, json=None, **kwargs):
    return request('post', url, data=data, json=json, **kwargs)
```
- **Behavior Provided:** When `json=` is passed, `requests` automatically calls `json.dumps()` on the dictionary AND sets the HTTP header `Content-Type: application/json; charset=utf-8`.
- **Backward Compatibility:** Passing a serialized string to `data=` (`data=json.dumps(...)`) was **not removed or deprecated at the Python interpreter level**. It still executes and sends raw string data over the wire.

### 2.2 The Documentation Corpus
In `docs/user/quickstart.rst` (under the section *"More complicated POST requests"*):
- **Pre-2.4.2 Documentation:**
  ```rst
  More complicated POST requests
  ------------------------------
  Typically, you want to send some form-encoded data — much like an HTML form. 
  To do this, simply pass a dictionary to the ``data`` argument...
  
  There are many times that you want to send data that is not form-encoded. 
  If you were to pass in an ``str`` instead of a ``dict``, that data will be posted directly.
  
  For example, the GitHub API v3 accepts JSON-Encoded POST/PATCH data:
  
      >>> import json
      >>> url = 'https://api.github.com/some/endpoint'
      >>> payload = {'some': 'data'}
      >>> r = requests.post(url, data=json.dumps(payload))
  ```
- **The Benchmark Sentence:**  
  `"To send JSON, explicitly serialize the string with data=json.dumps(payload)."`
- **Post-2.4.2 Documentation Update:**  
  Upstream Requests documentation was later updated to state:
  ```rst
  Instead of encoding the ``dict`` yourself, you can also pass it directly using 
  the ``json`` parameter (added in version 2.4.2) and it will be encoded automatically:
  
      >>> r = requests.post(url, json=payload)
  ```

---

## 3. Seven Forensic Verification Questions

### 1. Did the code change actually introduce native JSON support?
**YES.** PR #2258 / #2464 authentically introduced `json=None` to `post()`, `put()`, `patch()`, and `request()` in `requests/api.py` and `requests/sessions.py`.

### 2. What behaviour did the new parameter provide?
Automatic JSON serialization of Python dictionaries/lists, plus automatic injection of the `Content-Type: application/json` request header.

### 3. Does the documentation sentence explicitly require manual serialization, or merely describe one supported method?
The sentence states: *"To send JSON, explicitly serialize the string with data=json.dumps(payload)."* In natural language, this is an **imperative procedural instruction**. Before version 2.4.2, it described the *only* standard way to transmit JSON in Requests. After version 2.4.2, it became a legacy, sub-optimal workaround.

### 4. Was the sentence accurate before the code change?
**YES.** Prior to version 2.4.2, callers who wanted to send JSON had to serialize the data manually.

### 5. Did it become factually incorrect after the code change?
**Partially.** 
- From a strict execution perspective: `data=json.dumps(payload)` remains valid Python and transmits bytes.
- From a documentation engineering perspective: Claiming that callers *must explicitly serialize* JSON using `data=` became factually obsolete and misleading, as it omits the native API and fails to set the `Content-Type: application/json` header that modern APIs require.

### 6. Does updated documentation elsewhere already clarify the new functionality?
In the benchmark snapshot `files_head`, the quickstart documentation had not yet been updated. In real upstream history, Requests documentation added the `json=` note in a subsequent documentation revision.

### 7. Is there an actual contradiction, or only an additional capability?
There is an **additional capability that causes procedural documentation drift**. It is not a syntactically broken API contract (like removing a parameter or altering a default value), but an architectural improvement that renders existing documented practices obsolete.

---

## 4. Final Classification & Verdict

### Formal Classification: `PARTIALLY OUTDATED / BEHAVIORALLY SUPERSEDED`

Under strict scientific standards, `REAL-REQUESTS-01` should be classified as:
- **`PARTIALLY OUTDATED` (Procedural Drift / Best-Practice Invalidation)**

It is **NOT** a breaking syntactic contradiction (such as `PY-PARAM-002` or `PY-DEFAULT-001`). 

### Why Deterministic Analysis Could Not Detect It
Deterministic static analysis inspects syntax trees for equality and deletions:
- `data=None` was not removed.
- `post` was not removed or renamed.
- `json=None` is an optional additive parameter.
If a deterministic rule flagged every added keyword parameter as documentation drift, it would produce an unacceptable false-positive storm across virtually every non-breaking library release.

### What Semantic Inference Contributed
Qwen3-8B's semantic reasoning was able to connect the semantics of adding `json=None` with the documentation sentence advising `data=json.dumps(...)`. The model understood that adding native support superseded the manual serialization instruction.

### Evaluator Recommendation
`REAL-REQUESTS-01` demonstrates that local LLMs can detect **procedural and best-practice drift caused by additive features**. However, to maintain absolute scientific integrity:
1. It must not be conflated with hard syntactic breaks.
2. It should be classified as **Procedural / Behavioral Supersession Drift**.
3. It represents a valid, reproducible win for AI semantic reasoning, but on a softer semantic boundary than breaking API mutations.
