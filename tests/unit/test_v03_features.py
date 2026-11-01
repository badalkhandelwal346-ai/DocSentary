import tempfile
from pathlib import Path

from docsentry.contracts.code import CodeFact
from docsentry.contracts.docs import DocSpan
from docsentry.contracts.scan import ScanContext
from docsentry.extractors.markdown import MarkdownExtractor
from docsentry.git.diff import GitDiffService
from docsentry.git.runner import GitRunner
from docsentry.git.snapshots import GitSnapshotService
from docsentry.mapping.candidates import CandidateMapper
from docsentry.pipeline import Dependencies, path_matches_globs, scan_repository
from docsentry.rules.engine import DeterministicRuleEngine
from docsentry.rules.returns import detect_return_drift
from docsentry.validation.evidence import EvidenceValidator


def test_classify_all_eight_claims() -> None:
    me = MarkdownExtractor()

    # 1. code_example
    s_fence = me.extract("doc.md", "```python\nx = 1\n```")
    assert s_fence[0].claim_type == "code_example"

    # 2. historical_migration
    s_mig = me.extract("doc.md", "Previously in v1.0, this function returned None.")
    assert s_mig[0].claim_type == "historical_migration"

    # 3. version_specific
    s_ver = me.extract("doc.md", "Since v2.0, asynchronous streaming is the standard.")
    assert s_ver[0].claim_type == "version_specific"

    # 4. api_reference (table cell)
    s_table = me.extract("doc.md", "| Parameter | Type |\n| --- | --- |\n| `timeout` | `float` |")
    assert any(s.claim_type == "api_reference" for s in s_table)

    # 5. configuration_instruction
    s_cfg = me.extract("doc.md", "Set environment variable `DOCSENTRY_TIMEOUT` to configure limit.")
    assert s_cfg[0].claim_type == "configuration_instruction"

    # 6. procedural_instruction
    s_proc = me.extract("doc.md", "To send JSON, explicitly serialize the string with `data=json.dumps(payload)`.")
    assert s_proc[0].claim_type == "procedural_instruction"

    # 7. active_assertion
    s_act = me.extract("doc.md", "By default, timeout is 5.0 seconds.")
    assert s_act[0].claim_type == "active_assertion"

    # 8. general_description
    s_gen = me.extract("doc.md", "DocSentry is designed for software engineering teams.")
    assert s_gen[0].claim_type == "general_description"


def test_return_drift_rule_py_return_007() -> None:
    fact = CodeFact(
        fact_id="fact-1",
        language="python",
        path="src/response.py",
        symbol="read",
        kind="return_changed",
        category="behavioral",
        before="None",
        after="b''",
        line_before=10,
        line_after=10,
        source_change_id="diff",
        static_confidence="high",
    )
    span = DocSpan(
        span_id="span-1",
        path="docs/streaming.md",
        block_type="paragraph",
        text="Calling response.read() on an empty stream returns None.",
        raw_text="Calling response.read() on an empty stream returns None.",
        line_start=5,
        line_end=5,
        claim_type="active_assertion",
    )

    finding = detect_return_drift(fact, span, "DG-RET-001")
    assert finding is not None
    assert finding.status == "DRIFT"
    assert finding.rule_id == "PY-RETURN-007"
    assert "return contract changed from 'None' to 'b'''" in finding.explanation


def test_return_drift_rule_negative_control_updated_doc() -> None:
    fact = CodeFact(
        fact_id="fact-1",
        language="python",
        path="src/response.py",
        symbol="read",
        kind="return_changed",
        category="behavioral",
        before="None",
        after="b''",
        line_before=10,
        line_after=10,
        source_change_id="diff",
        static_confidence="high",
    )
    # Doc already updated to b''
    span = DocSpan(
        span_id="span-1",
        path="docs/streaming.md",
        block_type="paragraph",
        text="Calling response.read() on an empty stream returns b''.",
        raw_text="Calling response.read() on an empty stream returns b''.",
        line_start=5,
        line_end=5,
        claim_type="active_assertion",
    )

    finding = detect_return_drift(fact, span, "DG-RET-001")
    assert finding is None


def test_sibling_disambiguation_avoids_attribution_fp() -> None:
    fact = CodeFact(
        fact_id="fact-const-1",
        language="python",
        path="src/config.py",
        symbol="CONNECT_TIMEOUT",
        member="CONNECT_TIMEOUT",
        kind="constant_changed",
        before="3.0",
        after="5.0",
        line_before=1,
        line_after=1,
        source_change_id="diff",
        static_confidence="high",
        metadata={
            "sibling_constants": ["READ_TIMEOUT", "POOL_TIMEOUT"]
        },
    )

    # Documentation explicitly refers to a sibling constant
    span_sibling = DocSpan(
        span_id="span-read",
        path="docs/config.md",
        block_type="paragraph",
        text="The READ_TIMEOUT defaults to 3.0 seconds.",
        raw_text="The READ_TIMEOUT defaults to 3.0 seconds.",
        line_start=10,
        line_end=10,
        claim_type="active_assertion",
    )

    mapper = CandidateMapper(min_score=4.0)
    links = mapper.map([fact], [span_sibling])
    # Sibling penalty (-6.0) ensures it is not linked to CONNECT_TIMEOUT
    assert len(links) == 0


def test_cross_repository_scanning_and_abstention() -> None:
    with tempfile.TemporaryDirectory() as td:
        code_dir = Path(td) / "code"
        doc_dir = Path(td) / "docs"
        code_dir.mkdir()
        doc_dir.mkdir()

        cr = GitRunner(code_dir)
        cr.run(["init"])
        cr.run(["config", "user.name", "Test"])
        cr.run(["config", "user.email", "test@example.com"])
        (code_dir / "app.py").write_text("def old_helper(): pass\n")
        cr.run(["add", "."])
        cr.run(["commit", "-m", "init"])
        c_base = cr.resolve_sha("HEAD")

        (code_dir / "app.py").write_text("def new_helper(): pass\n")
        cr.run(["add", "."])
        cr.run(["commit", "-m", "remove old_helper"])
        c_head = cr.resolve_sha("HEAD")
        m_base = cr.get_merge_base(c_base, c_head)

        dr = GitRunner(doc_dir)
        dr.run(["init"])
        dr.run(["config", "user.name", "Test"])
        dr.run(["config", "user.email", "test@example.com"])
        (doc_dir / "guide.md").write_text("# Guide\n\nCall old_helper() to initialize.\n")
        dr.run(["add", "."])
        dr.run(["commit", "-m", "init doc"])
        d_head = dr.resolve_sha("HEAD")

        diff_s = GitDiffService(cr)
        snap_s = GitSnapshotService(cr)
        doc_snap_s = GitSnapshotService(dr)

        deps = Dependencies(
            git_diff_service=diff_s,
            git_snapshot_service=snap_s,
            markdown_extractor=MarkdownExtractor(),
            candidate_mapper=CandidateMapper(),
            rule_engine=DeterministicRuleEngine(),
            model_verifier=None,  # type: ignore
            evidence_validator=EvidenceValidator(snap_s, doc_snapshot_service=doc_snap_s),
        )

        # Mapped scan -> finds drift
        ctx_mapped = ScanContext(
            repo_root=code_dir,
            base_sha=c_base,
            head_sha=c_head,
            merge_base_sha=m_base,
            scan_id="cross-mapped",
            model_enabled=False,
            config_hash="h",
            tool_version="0.3.0",
            docs_repo_root=doc_dir,
            docs_head_sha=d_head,
        )
        report_mapped = scan_repository(ctx_mapped, deps)
        assert len(report_mapped.findings) == 1
        assert report_mapped.findings[0].rule_id == "PY-SYMBOL-003"

        # Unmapped scan -> abstains safely with warning
        ctx_unmapped = ScanContext(
            repo_root=code_dir,
            base_sha=c_base,
            head_sha=c_head,
            merge_base_sha=m_base,
            scan_id="cross-unmapped",
            model_enabled=False,
            config_hash="h",
            tool_version="0.3.0",
            docs_repo_root=doc_dir,
            docs_head_sha=None,
        )
        report_unmapped = scan_repository(ctx_unmapped, deps)
        assert len(report_unmapped.findings) == 0
        assert any("abstaining" in w for w in report_unmapped.warnings)


def test_path_matches_globs_root_file() -> None:
    assert path_matches_globs("index.py", ["**/*.py"]) is True
    assert path_matches_globs("src/client.py", ["**/*.py"]) is True
    assert path_matches_globs("README.md", ["**/*.md"]) is True
