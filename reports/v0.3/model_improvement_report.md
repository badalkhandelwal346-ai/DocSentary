# DocSentry v0.3: Model & Semantic Retrieval Improvement Report

**Target Version:** DocSentry v0.3.0  
**Date:** 2026-11-01  
**Focus:** Behavioral Contract Understanding, Relationship-Aware Retrieval, 8-Category Claim Classification & Bounded LLM Reasoning

---

## 1. Executive Summary

In DocSentry v0.2, the detection engine achieved high precision on syntactic changes (parameter removals, default shifts, removed symbols), but struggled with indirect behavioral drift (return value contracts, conceptual constant shifts, and procedural directives).

Version 0.3 resolves these limitations through four principled engineering enhancements:
1. **Behavioral Contract Understanding & Rule `PY-RETURN-007`:**
   Directly traces function return expressions (e.g. `None` $\rightarrow$ `b""`, `(data, errors)` $\rightarrow$ `data`) and flags explicit documented return-value contradictions deterministically.
2. **Relationship-Aware Retrieval & AST Call-Graph Propagation:**
   Connects module-level constants to their consuming functions and parameters (`DEFAULT_TIMEOUT` $\rightarrow$ `PoolManager.timeout`), while introducing sibling constant disambiguation (`READ_TIMEOUT` vs `CONNECT_TIMEOUT`) to prevent false-positive attribution.
3. **8-Category Documentation Claim Classification:**
   Expands claim classification from 4 crude types into 8 fine-grained semantic roles:
   `active_assertion`, `procedural_instruction`, `api_reference`, `configuration_instruction`, `code_example`, `historical_migration`, `version_specific`, and `general_description`.
4. **Structured Bounded AI Reasoning (`claim_status`):**
   Constrains Qwen3-8B to evaluate and report whether a claim is:
   - `contradicted` (Breaking behavioral falsehood $\rightarrow$ `DRIFT`)
   - `partially_outdated` (Procedural advice superseded by native parameter $\rightarrow$ `POTENTIAL_DRIFT`)
   - `incomplete_new_capability` (Additive feature, existing usage remains valid $\rightarrow$ `NO_DRIFT`)
   - `still_accurate` (Internal optimization, doc remains true $\rightarrow$ `NO_DRIFT`)
   - `historical` (Version notes, changelogs, migrations $\rightarrow$ `NO_DRIFT`)
   - `uncertain` (Ambiguous context $\rightarrow$ `UNCERTAIN` - Abstain)

---

## 2. Deep Dive: Behavioral Contract Understanding & `PY-RETURN-007`

### Problem
Previously, when a function's return contract changed (such as `HTTPResponse.read()` returning `b""` instead of `None` in `urllib3`, or `Schema.dump()` returning a dict instead of a 2-tuple in `marshmallow`), the AST extractor recorded `return_changed`, but the deterministic engine lacked a rule to evaluate it against Markdown text.

### Implementation
Rule `PY-RETURN-007` was introduced in `src/docsentry/rules/returns.py`:
- Validates that the documentation span explicitly references the target function and asserts the previous return expression (`None`, `b""`, `(result, errors)`).
- Checks whether the document has already been updated to state the new return contract.
- Produces a high-confidence deterministic `DRIFT` finding with verified code and doc evidence.

```python
# Code Diff:
- return None
+ return b''

# Documentation Assertion:
"Calling response.read() on an empty body returns None."

# DocSentry v0.3 Output:
[DRIFT] PY-RETURN-007: Documented return value for 'read' is outdated
Explanation: Function 'read' return contract changed from 'None' to 'b''' in src/urllib3/response.py, but documentation still claims it returns 'None'.
```

---

## 3. Relationship-Aware Retrieval & Call-Graph Propagation

### Call-Site Parameter Linkage
In `ASTVisitor._record_function`, when a parameter default references a module constant (`def connect(timeout=DEFAULT_TIMEOUT)`), the extractor records:
- Parameter name: `timeout`
- Function / Class name: `connect`
- Scope: `HTTPConnectionPool`

This allows `CandidateMapper` to match prose such as *"pool timeout"* or *"connection timeout"* against `DEFAULT_TIMEOUT` with a score of $+4.0$, bridging vocabulary gaps without resorting to ungrounded keyword matching.

### Sibling Disambiguation
To prevent false-positive drift alerts when multiple similar constants or parameters exist in the same module (`CONNECT_TIMEOUT`, `READ_TIMEOUT`, `POOL_TIMEOUT`):
- If the documentation text explicitly mentions a sibling symbol but does not mention the changed symbol, `CandidateMapper` applies a $-6.0$ penalty, rejecting the candidate pair.

---

## 4. Documentation Claim Classification (8 Categories)

| Claim Category | Definition & Key Indicators | Gating Behavior in Pipeline |
|---|---|---|
| `active_assertion` | Concrete factual assertion (`"defaults to"`, `"returns"`, `"raises"`, `"timeout is"`) | Primary target for deterministic rules and AI verification. |
| `procedural_instruction` | Imperative action guidance (`"To send JSON..."`, `"Configure X..."`, `"Pass Y..."`) | Evaluated for procedural drift (`POTENTIAL_DRIFT`). |
| `api_reference` | Parameter tables, signatures, type definitions | High affinity for signature and return-type checks. |
| `configuration_instruction` | Env vars (`DOCSENTRY_*`), CLI flags (`--repo`), setting definitions | High affinity for config flag and constant checks. |
| `code_example` | Fenced code blocks, illustrative call syntax | Default checks filtered out to prevent false positives. |
| `historical_migration` | Changelogs, release notes, migration guides (`"prior to v1.0"`) | Automatically penalized (-6.0); never flagged as drift. |
| `version_specific` | Explicit version anchors (`"Since v2.0..."`, `"As of v1.5..."`) | Filtered out unless code diff targets that specific version. |
| `general_description` | High-level conceptual prose and background descriptions | Bypassed; lowest candidate affinity. |

---

## 5. Structured Bounded AI Reasoning with Qwen3-8B

When candidates reach `SemanticModelVerifier`, Qwen3-8B is presented with a bounded JSON schema enforcing strict categorization:

```json
{
  "status": "DRIFT | POTENTIAL_DRIFT | NO_DRIFT | UNCERTAIN",
  "claim_status": "contradicted | partially_outdated | incomplete_new_capability | still_accurate | historical | uncertain",
  "severity": "high | medium | low | info",
  "explanation": "One or two concise sentences.",
  "evidence_ids": ["CODE-1", "DOC-1"],
  "reasoning_type": "direct_contradiction | likely_outdated | no_change | insufficient_context",
  "suggested_action": "Actionable advice for the engineer"
}
```

### Safety & Abstention Guarantee
1. **Never Invent Evidence:** If the code or documentation quotes do not exist in the Git snapshot, `EvidenceValidator` downgrades the finding to `UNCERTAIN`.
2. **Conservative Fallback:** If the model generates an ambiguous response or the LLM endpoint is unreachable, DocSentry marks the candidate `UNCERTAIN` and omits it from the report.
