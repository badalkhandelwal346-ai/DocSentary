import fnmatch
import time
from pathlib import Path
from typing import NamedTuple

from docsentry.ai.verifier import SemanticModelVerifier
from docsentry.contracts.code import CodeFact
from docsentry.contracts.diff import ChangedFile
from docsentry.contracts.docs import DocSpan
from docsentry.contracts.findings import ScanReport
from docsentry.contracts.scan import ScanContext
from docsentry.extractors.markdown import MarkdownExtractor
from docsentry.extractors.python_ast import compare_python_facts
from docsentry.git.diff import GitDiffService
from docsentry.git.snapshots import GitSnapshotService
from docsentry.mapping.candidates import CandidateMapper
from docsentry.rules.engine import DeterministicRuleEngine
from docsentry.validation.evidence import EvidenceValidator


class Dependencies(NamedTuple):
    git_diff_service: GitDiffService
    git_snapshot_service: GitSnapshotService
    markdown_extractor: MarkdownExtractor
    candidate_mapper: CandidateMapper
    rule_engine: DeterministicRuleEngine
    model_verifier: SemanticModelVerifier
    evidence_validator: EvidenceValidator


def path_matches_globs(path: str, globs: list[str]) -> bool:
    clean_p = path.replace("\\", "/")
    p_name = Path(clean_p).name
    for g in globs:
        if fnmatch.fnmatch(clean_p, g) or fnmatch.fnmatch(p_name, g):
            return True
        if g.startswith("**/") and (
            fnmatch.fnmatch(clean_p, g[3:]) or fnmatch.fnmatch(p_name, g[3:])
        ):
            return True
    return False


def scan_repository(context: ScanContext, deps: Dependencies) -> ScanReport:
    """
    Executes the end-to-end DocGuard analysis pipeline.
    """
    start_time = time.perf_counter()
    warnings: list[str] = []

    # 1. Resolve diff between merge-base and head
    all_changed_files = deps.git_diff_service.get_changed_files(
        context.merge_base_sha, context.head_sha
    )

    # 2. Filter files according to scope & exclusions
    active_changed_files: list[ChangedFile] = []
    code_facts: list[CodeFact] = []

    for cf in all_changed_files:
        primary_path = cf.path_after or cf.path_before or ""

        # Check exclusions
        if path_matches_globs(primary_path, context.exclude_globs):
            warnings.append(f"Excluded file: {primary_path}")
            continue

        active_changed_files.append(cf)

        # If Python file, extract code facts
        if path_matches_globs(primary_path, context.source_globs):
            before_content = (
                deps.git_snapshot_service.read_file(context.merge_base_sha, cf.path_before)
                if cf.path_before
                else None
            )
            after_content = (
                deps.git_snapshot_service.read_file(context.head_sha, cf.path_after)
                if cf.path_after
                else None
            )

            file_facts = compare_python_facts(
                path=primary_path,
                before_source=before_content,
                after_source=after_content,
            )
            code_facts.extend(file_facts)

    # 3. Extract documentation spans from HEAD snapshot for markdown files
    doc_spans: list[DocSpan] = []
    docs_service = deps.git_snapshot_service
    docs_head = context.head_sha

    if context.docs_repo_root:
        from docsentry.git.runner import GitRunner
        # Verify cross-repository revision mapping
        resolved_doc_sha = context.docs_head_sha
        if not resolved_doc_sha and context.docs_revision_mapping:
            resolved_doc_sha = context.docs_revision_mapping.get(context.head_sha)

        if not resolved_doc_sha:
            warnings.append(
                f"Cross-repository revision mapping not established between code revision "
                f"{context.head_sha[:8]} and doc repository {context.docs_repo_root}; "
                "abstaining from cross-repository drift detection to avoid false positives."
            )
        else:
            docs_runner = GitRunner(context.docs_repo_root)
            docs_service = GitSnapshotService(docs_runner)
            docs_head = resolved_doc_sha
            for glob_pattern in context.docs_globs:
                for doc_file in context.docs_repo_root.glob(glob_pattern):
                    if doc_file.is_file():
                        rel_path = str(doc_file.relative_to(context.docs_repo_root)).replace("\\", "/")
                        if not path_matches_globs(rel_path, context.exclude_globs):
                            if not any(s.path == rel_path for s in doc_spans):
                                content = docs_service.read_file(docs_head, rel_path)
                                if content:
                                    doc_spans.extend(deps.markdown_extractor.extract(rel_path, content))
    else:
        # Same repository extraction
        for cf in active_changed_files:
            p = cf.path_after or ""
            if p and path_matches_globs(p, context.docs_globs):
                content = deps.git_snapshot_service.read_file(context.head_sha, p)
                if content:
                    doc_spans.extend(deps.markdown_extractor.extract(p, content))

        for glob_pattern in context.docs_globs:
            for doc_file in context.repo_root.glob(glob_pattern):
                if doc_file.is_file():
                    rel_path = str(doc_file.relative_to(context.repo_root)).replace("\\", "/")
                    if not path_matches_globs(rel_path, context.exclude_globs):
                        if not any(s.path == rel_path for s in doc_spans):
                            content = deps.git_snapshot_service.read_file(context.head_sha, rel_path)
                            if content:
                                doc_spans.extend(deps.markdown_extractor.extract(rel_path, content))

    # 4. Candidate mapping
    candidates = deps.candidate_mapper.map(code_facts, doc_spans)

    # 5. Deterministic rule evaluation
    deterministic_findings = deps.rule_engine.evaluate(code_facts, doc_spans, candidates)

    covered_doc_spans = {
        (ev.path, ev.line_start)
        for f in deterministic_findings
        for ev in f.evidence
        if ev.role == "documentation"
    }

    # 6. Optional AI verifier for remaining behavioral candidates
    ai_findings = []
    if context.model_enabled:
        ai_findings = deps.model_verifier.verify_candidates(
            code_facts, doc_spans, candidates, covered_doc_spans
        )

    all_raw_findings = deterministic_findings + ai_findings

    # 7. Evidence validation trust boundary
    validated_findings = deps.evidence_validator.validate_findings(
        all_raw_findings, context.head_sha, docs_head_sha=docs_head
    )

    duration_ms = int((time.perf_counter() - start_time) * 1000)

    drift_count = sum(1 for f in validated_findings if f.status == "DRIFT")
    potential_count = sum(1 for f in validated_findings if f.status == "POTENTIAL_DRIFT")
    uncertain_count = sum(1 for f in validated_findings if f.status == "UNCERTAIN")

    report = ScanReport(
        schema_version="1.0",
        scan_id=context.scan_id,
        base_sha=context.base_sha,
        head_sha=context.head_sha,
        merge_base_sha=context.merge_base_sha,
        tool_version=context.tool_version,
        model_id="organizer-open-weight-verifier" if context.model_enabled else None,
        summary={
            "changed_files": len(active_changed_files),
            "code_facts": len(code_facts),
            "doc_spans": len(doc_spans),
            "findings": len(validated_findings),
            "drift": drift_count,
            "potential_drift": potential_count,
            "uncertain": uncertain_count,
        },
        changed_files=active_changed_files,
        findings=validated_findings,
        warnings=warnings,
        duration_ms=duration_ms,
    )

    return report
