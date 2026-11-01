from pathlib import Path

from backend.app.adapters.engine_adapter import DocSentryEngineAdapter
from docsentry.contracts.findings import EvidenceRef, Finding, ScanReport


def test_engine_adapter_normalization():
    adapter = DocSentryEngineAdapter()

    # Construct a synthetic ScanReport
    evidence_doc = EvidenceRef(
        evidence_id="ev-1",
        role="documentation",
        path="README.md",
        line_start=15,
        line_end=17,
        quote="Default timeout is 30.",
        source_kind="doc_span",
    )
    evidence_code = EvidenceRef(
        evidence_id="ev-2",
        role="code",
        path="src/client.py",
        line_start=10,
        line_end=12,
        quote="timeout: int = 60",
        source_kind="ast_fact",
    )

    finding = Finding(
        finding_id="f-test-1",
        status="DRIFT",
        severity="high",
        rule_id="RULE_PARAM_DEFAULT_CHANGED",
        category="signature_drift",
        title="Default timeout changed",
        explanation="Default timeout updated to 60 in code but docs say 30.",
        evidence=[evidence_doc, evidence_code],
        confidence=1.0,
        verification="deterministic",
        suggested_action="Update README.md to 60.",
    )

    report = ScanReport(
        scan_id="scan-12345",
        base_sha="abcdef1",
        head_sha="abcdef2",
        merge_base_sha="abcdef1",
        tool_version="0.2.0",
        model_id=None,
        summary={"drift": 1, "changed_files": 1},
        changed_files=[],
        findings=[finding],
        warnings=[],
        duration_ms=250,
    )

    normalized = adapter.normalize_report(report)

    assert normalized.success is True
    assert normalized.scan_id == "scan-12345"
    assert normalized.duration_ms == 250
    assert len(normalized.findings) == 1

    nf = normalized.findings[0]
    assert nf.external_id == "f-test-1"
    assert nf.status == "DRIFT"
    assert nf.rule_id == "RULE_PARAM_DEFAULT_CHANGED"
    assert len(nf.evidence) == 2

    ne_doc = [e for e in nf.evidence if e.role == "documentation"][0]
    assert ne_doc.path == "README.md"
    assert ne_doc.line_start == 15
    assert ne_doc.quote == "Default timeout is 30."


def test_engine_adapter_handles_invalid_git_ref_safely(tmp_path: Path):
    adapter = DocSentryEngineAdapter()
    result = adapter.execute_scan(
        repo_path=tmp_path,
        base_sha="nonexistent_base",
        head_sha="nonexistent_head",
    )

    assert result.success is False
    assert result.error_message is not None
    assert "Git Error" in result.error_message or "Analysis failed" in result.error_message
