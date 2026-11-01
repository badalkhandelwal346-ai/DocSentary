import concurrent.futures
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from docsentry import __version__
from docsentry.ai.client import ModelClient
from docsentry.ai.verifier import SemanticModelVerifier
from docsentry.config import load_config
from docsentry.contracts.findings import ScanReport
from docsentry.contracts.scan import ScanContext
from docsentry.extractors.markdown import MarkdownExtractor
from docsentry.git.diff import GitDiffService
from docsentry.git.errors import GitError
from docsentry.git.runner import GitRunner
from docsentry.git.snapshots import GitSnapshotService
from docsentry.mapping.candidates import CandidateMapper
from docsentry.pipeline import Dependencies, scan_repository
from docsentry.rules.engine import DeterministicRuleEngine
from docsentry.validation.evidence import EvidenceValidator


@dataclass
class NormalizedEvidence:
    external_id: str
    role: str
    path: str
    line_start: int
    line_end: int
    quote: str
    source_kind: str
    metadata_json: Optional[Dict[str, Any]] = None


@dataclass
class NormalizedFinding:
    external_id: str
    status: str
    severity: str
    rule_id: str
    category: str
    title: str
    explanation: str
    confidence: Optional[float]
    verification: str
    suggested_action: Optional[str]
    evidence: List[NormalizedEvidence] = field(default_factory=list)


@dataclass
class NormalizedScanResult:
    scan_id: str
    base_sha: str
    head_sha: str
    merge_base_sha: str
    tool_version: str
    model_id: Optional[str]
    duration_ms: int
    summary: Dict[str, Any]
    findings: List[NormalizedFinding] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None


class DocSentryEngineAdapter:
    """
    Adapter bridging the backend application services to the Track A DocSentry core engine.
    Ensures zero modification to existing detection engine and isolates repository scanning.
    """

    def __init__(self, default_timeout_seconds: int = 120):
        self.default_timeout_seconds = default_timeout_seconds

    def execute_scan(
        self,
        repo_path: Path,
        base_sha: str,
        head_sha: str,
        config_path: Optional[Path] = None,
        no_model: bool = False,
        timeout_seconds: Optional[int] = None,
        clone_url: Optional[str] = None,
    ) -> NormalizedScanResult:
        """
        Executes scan_repository synchronously or with timeout protection.
        Supports transient shallow clone if a remote clone_url is provided.
        """
        timeout = timeout_seconds or self.default_timeout_seconds
        start_time = time.perf_counter()
        temp_dir_ctx = None
        target_path = repo_path

        try:
            if clone_url and (not (repo_path / ".git").exists()):
                import subprocess
                import tempfile
                temp_dir_ctx = tempfile.TemporaryDirectory()
                target_path = Path(temp_dir_ctx.name)
                subprocess.run(
                    ["git", "clone", "--depth", "50", clone_url, str(target_path)],
                    check=False,
                    capture_output=True,
                    timeout=timeout or 60,
                )

            # 1. Config loading
            resolved_config_path = config_path
            if resolved_config_path is None:
                if (target_path / "docsentry.yml").exists():
                    resolved_config_path = target_path / "docsentry.yml"
                elif (target_path / "docguard.yml").exists():
                    resolved_config_path = target_path / "docguard.yml"

            cfg, cfg_hash = load_config(resolved_config_path)

            # 2. Git validation and SHA resolution
            runner = GitRunner(target_path, timeout_seconds=cfg.model.timeout_seconds)
            runner.validate_commit(base_sha)
            runner.validate_commit(head_sha)
            resolved_base_sha = runner.resolve_sha(base_sha)
            resolved_head_sha = runner.resolve_sha(head_sha)
            merge_base_sha = runner.get_merge_base(resolved_base_sha, resolved_head_sha)

            # 3. Build ScanContext
            scan_id = f"scan-{uuid.uuid4().hex[:12]}"
            context = ScanContext(
                repo_root=target_path,
                base_sha=resolved_base_sha,
                head_sha=resolved_head_sha,
                merge_base_sha=merge_base_sha,
                scan_id=scan_id,
                source_globs=cfg.scope.source_globs,
                docs_globs=cfg.scope.docs_globs,
                exclude_globs=cfg.scope.exclude_globs,
                model_enabled=not no_model and cfg.model.enabled,
                config_hash=cfg_hash,
                tool_version=__version__,
            )

            # 4. Construct Dependencies
            diff_service = GitDiffService(runner)
            snapshot_service = GitSnapshotService(runner, max_file_bytes=cfg.limits.max_file_bytes)
            markdown_extractor = MarkdownExtractor()
            candidate_mapper = CandidateMapper(top_k=cfg.limits.max_doc_spans_per_fact)
            rule_engine = DeterministicRuleEngine()
            model_verifier = SemanticModelVerifier(ModelClient())
            evidence_validator = EvidenceValidator(snapshot_service)

            deps = Dependencies(
                git_diff_service=diff_service,
                git_snapshot_service=snapshot_service,
                markdown_extractor=markdown_extractor,
                candidate_mapper=candidate_mapper,
                rule_engine=rule_engine,
                model_verifier=model_verifier,
                evidence_validator=evidence_validator,
            )

            # 5. Execute engine with timeout protection
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(scan_repository, context, deps)
                raw_report: ScanReport = future.result(timeout=timeout)

            # 6. Normalize ScanReport
            return self.normalize_report(raw_report)

        except concurrent.futures.TimeoutError:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return NormalizedScanResult(
                scan_id=f"scan-timeout-{uuid.uuid4().hex[:8]}",
                base_sha=base_sha,
                head_sha=head_sha,
                merge_base_sha=base_sha,
                tool_version=__version__,
                model_id=None,
                duration_ms=duration_ms,
                summary={"error": "timeout"},
                success=False,
                error_message=f"DocSentry analysis timed out after {timeout} seconds",
            )
        except GitError as git_err:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return NormalizedScanResult(
                scan_id=f"scan-err-{uuid.uuid4().hex[:8]}",
                base_sha=base_sha,
                head_sha=head_sha,
                merge_base_sha=base_sha,
                tool_version=__version__,
                model_id=None,
                duration_ms=duration_ms,
                summary={"error": "git_error"},
                success=False,
                error_message=f"Git Error during scan: {git_err.stderr or str(git_err)}",
            )
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            return NormalizedScanResult(
                scan_id=f"scan-err-{uuid.uuid4().hex[:8]}",
                base_sha=base_sha,
                head_sha=head_sha,
                merge_base_sha=base_sha,
                tool_version=__version__,
                model_id=None,
                duration_ms=duration_ms,
                summary={"error": "general_error"},
                success=False,
                error_message=f"Analysis failed: {str(exc)}",
            )
        finally:
            if temp_dir_ctx:
                try:
                    temp_dir_ctx.cleanup()
                except Exception:
                    pass

    def normalize_report(self, report: ScanReport) -> NormalizedScanResult:
        """
        Converts a canonical ScanReport Pydantic object into a NormalizedScanResult.
        """
        normalized_findings: List[NormalizedFinding] = []

        for f in report.findings:
            normalized_evidence: List[NormalizedEvidence] = []
            for ev in f.evidence:
                normalized_evidence.append(
                    NormalizedEvidence(
                        external_id=ev.evidence_id,
                        role=ev.role,
                        path=ev.path,
                        line_start=ev.line_start,
                        line_end=ev.line_end,
                        quote=ev.quote,
                        source_kind=ev.source_kind,
                        metadata_json=None,
                    )
                )

            normalized_findings.append(
                NormalizedFinding(
                    external_id=f.finding_id,
                    status=f.status,
                    severity=f.severity,
                    rule_id=f.rule_id,
                    category=f.category,
                    title=f.title,
                    explanation=f.explanation,
                    confidence=f.confidence,
                    verification=f.verification,
                    suggested_action=f.suggested_action,
                    evidence=normalized_evidence,
                )
            )

        return NormalizedScanResult(
            scan_id=report.scan_id,
            base_sha=report.base_sha,
            head_sha=report.head_sha,
            merge_base_sha=report.merge_base_sha,
            tool_version=report.tool_version,
            model_id=report.model_id,
            duration_ms=report.duration_ms,
            summary=dict(report.summary),
            findings=normalized_findings,
            warnings=list(report.warnings),
            success=True,
            error_message=None,
        )
