# DocSentry v0.2.1: Regression Coverage Audit & Adversarial Invariant Testing

**Evaluation Date:** 2026-11-01  
**Audit Scope:** Dedicated Unit, Regression, and Adversarial Invariant Test Suite  
**Test Module:** `tests/unit/test_v021_regression.py` (12 Dedicated Test Cases)  
**Total Suite Status:** 58 passed in 1.98s (`pytest -q`) | Ruff clean  

---

## 1. Executive Summary & Verification Objective

In Phase 3 of the v0.2.1 independent validation, the four repaired failure modes identified during the v0.2 forensic analysis were subjected to formal regression testing:
1. **Failure Mode 1:** Imperative procedural documentation claim classification (`MarkdownExtractor`).
2. **Failure Mode 2:** Typed class attribute extraction via `visit_AnnAssign` in `ASTVisitor`.
3. **Failure Mode 3:** Class-body variable assignment extraction and deletion tracking (`visit_Assign` scope guard).
4. **Failure Mode 4:** Environment variable lookup extraction (`os.environ.get()` and `os.getenv()`).

To guard against over-fitting and false-positive regressions, the test suite was expanded with an **Adversarial Robustness Matrix** testing whether the new extraction rules erroneously generate false alarms on internal attributes, unreferenced environment variables, or unchanged procedural docs.

---

## 2. Regression Coverage for the Four Repaired Failure Modes

### 2.1 Failure Mode 1: Imperative Procedural Documentation
- **Issue in Baseline:** Procedural sentences such as `"To send JSON, explicitly serialize the string with data=json.dumps(payload)."` were categorized as `general_description` because they lacked passive keywords (e.g. `"default"`, `"returns"`), causing the AI routing filter to discard them.
- **Positive Test (`test_fm1_imperative_procedural_doc_positive`):**
  - Input: `"To send JSON, explicitly serialize the string with data=json.dumps(payload)."`
  - Expected Classification: `active_assertion`
  - Result: **PASSED**
- **Negative Control (`test_fm1_general_conceptual_doc_negative_control`):**
  - Input: `"JSON is a language-independent data format widely supported on the web."`
  - Expected Classification: `general_description`
  - Result: **PASSED**

---

### 2.2 Failure Mode 2: Typed Class Attributes (`ast.AnnAssign`)
- **Issue in Baseline:** Modern typed class attributes (e.g., Pydantic v2 `class ConfigDict: orm_mode: bool = False`) were unhandled because `ASTVisitor` had no `visit_AnnAssign` method.
- **Positive Test (`test_fm2_typed_class_attribute_annassign_positive`):**
  - Input Diff: `orm_mode: bool = False` $\rightarrow$ `from_attributes: bool = False` inside `class ConfigDict:`
  - Expected Extracted Fact: `CodeFact(kind="function_removed", member="orm_mode", qualified_name="ConfigDict.orm_mode")`
  - Result: **PASSED**
- **Negative Control (`test_fm2_typed_class_attribute_unchanged_negative_control`):**
  - Input: Identical base and head source code with typed attributes.
  - Expected Facts: `[]` (0 facts extracted)
  - Result: **PASSED**

---

### 2.3 Failure Mode 3: Class-Body Assignments (`visit_Assign` Scope Guard)
- **Issue in Baseline:** `ASTVisitor.visit_Assign` had an explicit check `if not self.scope_stack:` which silently bypassed all variable assignments inside class definitions (e.g., `class Flask: json_encoder = json.JSONEncoder`).
- **Positive Test (`test_fm3_class_body_assignment_removal_positive`):**
  - Input Diff: Removal of `json_encoder = json.JSONEncoder` from `class Flask:`
  - Expected Extracted Fact: `CodeFact(kind="function_removed", symbol="Flask.json_encoder", member="json_encoder")`
  - Result: **PASSED**
- **Negative Control (`test_fm3_class_body_assignment_unchanged_negative_control`):**
  - Input: Identical class body assignment across base and head.
  - Expected Facts: `[]`
  - Result: **PASSED**

---

### 2.4 Failure Mode 4: Environment Variable Configuration Lookups
- **Issue in Baseline:** Code loading configuration via `os.environ.get('FLASK_ENV', 'production')` was ignored because the target identifier was lowercase (`env`) and `os.environ` calls were not recognized as configuration flags.
- **Positive Test A (`test_fm4_os_environ_get_positive`):**
  - Input Diff: `env = os.environ.get('FLASK_ENV', 'production')` $\rightarrow$ `env = 'production'`
  - Expected Extracted Fact: `CodeFact(kind="config_flag_changed", member="FLASK_ENV", before="FLASK_ENV", after=None)`
  - Result: **PASSED**
- **Positive Test B (`test_fm4_os_getenv_positive`):**
  - Input Diff: `debug = os.getenv('APP_DEBUG', 'False')` $\rightarrow$ `debug = 'False'`
  - Expected Extracted Fact: `CodeFact(kind="config_flag_changed", member="APP_DEBUG")`
  - Result: **PASSED**

---

## 3. Adversarial Invariant Robustness Suite

| Adversarial Scenario | Test Description & Input State | Expected Invariant | Test Function | Result |
|:---|:---|:---|:---|:---:|
| **1. Internal Private Attribute** | `_internal_cache: dict = {}` changed inside class; documentation describes public class. | `detect_symbol_drift()` must return `None`. Zero false alarms on private internal implementation details. | `test_adv_internal_private_class_attribute_not_drifted` | **PASSED** |
| **2. Unreferenced Env Variable** | Variable mentioned only in comments or string literals (e.g. `# Remember to set FLASK_ENV`). | `extract_python_module_facts()` must NOT add the token to `cli_flags`. | `test_adv_env_var_in_comment_or_string_never_extracted` | **PASSED** |
| **3. Unchanged Config Flag** | `os.environ.get('PORT', '8000')` present identically in base and head. | `compare_python_facts()` must yield 0 facts. | `test_adv_unchanged_env_var_produces_no_facts` | **PASSED** |
| **4. Unrelated Code Mutation** | Function `unrelated()` modified; procedural doc describes JSON serialization. | Rule engine must return `None`. Unrelated code changes must never invalidate procedural docs. | `test_adv_procedural_doc_remains_correct_when_unrelated_code_changes` | **PASSED** |

---

## 4. Test Suite Execution & Stability Summary

- **Total Test Cases in Suite:** 58
- **New Dedicated Tests Added:** 12
- **Test Failures:** 0
- **Regression Execution Time:** 0.10s
- **Full Suite Execution Time:** 1.98s
- **Linter & Style Validation:** 100% compliant (`ruff check .`)
