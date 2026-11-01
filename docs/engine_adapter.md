# DocSentry — Engine Adapter Specification
**Version:** 0.2.0-adapter  
**Integration Boundary:** Decoupled Adapter between FastAPI Backend and Track A Detection Engine

---

## 1. Architectural Intent

The DocSentry core intelligence engine was developed in Track A to execute documentation drift analysis via the CLI (`docsentry scan`) and benchmark suites. Track A encompasses:
- `docsentry.pipeline.scan_repository`: Core pipeline execution function.
- `docsentry.extractors.python_ast`: Static AST extraction comparing before/after syntax trees.
- `docsentry.extractors.markdown`: Markdown parsing and claim classification.
- `docsentry.rules.engine`: Deterministic rule evaluation.
- `docsentry.ai.verifier`: Semantic LLM verification (Qwen3-8B).
- `docsentry.validation.evidence`: Evidence trust boundary and provenance validation.

To preserve the stability, reproducibility, and benchmark integrity of Track A, **the backend must never modify these modules**. Instead, all interaction occurs via `DocSentryEngineAdapter`.

---

## 2. Adapter Architecture

```
+-------------------------------------------------------------------------+
|                          FASTAPI SERVICE LAYER                          |
|                     (AnalysisService.trigger_scan)                      |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                        DOCSENTRY ENGINE ADAPTER                         |
|                                                                         |
|  1. Input Sanitization & Path Preparation                               |
|     - Validates repository root contains valid .git repository          |
|     - Verifies base SHA and head SHA exist                              |
|     - Merges repository config overrides with default `docsentry.yml`   |
|                                                                         |
|  2. ScanContext & Dependencies Construction                             |
|     - Instantiates GitDiffService, GitSnapshotService, MarkdownExtractor|
|     - Configures DeterministicRuleEngine and SemanticModelVerifier      |
|     - Configures EvidenceValidator with active rules                    |
|                                                                         |
|  3. Safe Execution & Timeout Shield                                     |
|     - Executes `pipeline.scan_repository(context, deps)`                |
|     - Traps GitError, AST parse exceptions, and timeout interrupts      |
|                                                                         |
|  4. Output Normalization                                                |
|     - Converts Pydantic `ScanReport` to database entity representations |
|     - Extracts and normalizes `Finding` and `Evidence` models           |
|     - Computes summary counts, duration metrics, and warnings           |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                       TRACK A: PIPELINE.PY (FROZEN)                     |
+-------------------------------------------------------------------------+
```

---

## 3. Data Flow & Contract Mapping

### Input: `ScanRequest`
```python
@dataclass(frozen=True)
class EngineScanRequest:
    repo_path: Path
    base_sha: str
    head_sha: str
    merge_base_sha: str | None = None
    config_overrides: dict[str, Any] | None = None
    no_model: bool = False
    timeout_seconds: int = 120
```

### Output: `NormalizedScanResult`
The adapter maps the native `ScanReport` into a structure directly consumable by the database session:

```python
@dataclass
class NormalizedFinding:
    external_id: str
    status: str
    severity: str
    rule_id: str
    category: str
    title: str
    explanation: str
    confidence: float | None
    verification: str
    suggested_action: str | None
    evidence: list[NormalizedEvidence]

@dataclass
class NormalizedEvidence:
    external_id: str
    role: str
    path: str
    line_start: int
    line_end: int
    quote: str
    source_kind: str
    metadata: dict[str, Any]

@dataclass
class NormalizedScanResult:
    scan_id: str
    base_sha: str
    head_sha: str
    merge_base_sha: str
    tool_version: str
    model_id: str | None
    duration_ms: int
    summary: dict[str, Any]
    findings: list[NormalizedFinding]
    warnings: list[str]
    success: bool
    error_message: str | None = None
```

---

## 4. Error Handling & Edge Cases

| Failure Mode | Engine Behavior | Adapter Mitigation |
|---|---|---|
| **Git Ref Missing** | Raises `GitError: revision not found` | Traps `GitError`, sets `AnalysisRun.status = 'failed'`, records clear error message without crashing worker. |
| **Non-Python / Empty PR** | `changed_files` contains 0 code files | Returns empty findings list with warning `No Python files changed in diff`. Marks run as `completed`. |
| **Markdown Parse Error** | Markdown extractor skips malformed spans | Logs warning in `warnings` list; processes valid markdown spans. |
| **Model Verifier Offline** | LLM verifier fails connection | Falls back to deterministic rule results; marks finding provenance as `DETERMINISTIC`. |
| **Timeout Exceeded** | Thread/Process hangs on large repository | Enforces `timeout_seconds` via thread pool future, aborts scan, and marks `status = 'failed'`. |

---

## 5. Verification & Test Isolation

The engine adapter is tested via dedicated unit and integration tests (`backend/tests/test_engine_adapter.py`) using:
1. Real git repository test fixtures with known before/after commits.
2. In-memory synthetic `ScanReport` fixtures.
3. Verification that CLI commands (`python -m docsentry.cli scan`) produce identical reports to the adapter's output for identical git inputs.
