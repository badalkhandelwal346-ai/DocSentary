from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.adapters.engine_adapter import DocSentryEngineAdapter, NormalizedScanResult
from backend.app.db.models.analysis_run import AnalysisRun
from backend.app.db.models.evidence import Evidence
from backend.app.db.models.finding import Finding
from backend.app.db.models.repository import Repository
from backend.app.schemas.analysis import AnalysisRunResponse


class AnalysisService:
    @staticmethod
    def create_analysis_run(
        db: Session,
        organization_id: str,
        repository_id: str,
        pull_request_id: Optional[str],
        trigger_type: str,
        base_sha: str,
        head_sha: str,
        merge_base_sha: Optional[str] = None,
    ) -> AnalysisRun:
        run = AnalysisRun(
            organization_id=organization_id,
            repository_id=repository_id,
            pull_request_id=pull_request_id,
            trigger_type=trigger_type,
            status="queued",
            base_sha=base_sha,
            head_sha=head_sha,
            merge_base_sha=merge_base_sha or base_sha,
            tool_version="0.2.0",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def get_analysis_run(
        db: Session, organization_id: str, run_id: str
    ) -> Optional[AnalysisRunResponse]:
        run = db.scalar(
            select(AnalysisRun).where(
                AnalysisRun.id == run_id,
                AnalysisRun.organization_id == organization_id,
            )
        )
        if not run:
            return None
        return AnalysisRunResponse.model_validate(run)

    @staticmethod
    def list_analyses_for_repo(
        db: Session, organization_id: str, repository_id: str
    ) -> List[AnalysisRunResponse]:
        repo = db.scalar(
            select(Repository).where(
                Repository.id == repository_id,
                Repository.organization_id == organization_id,
            )
        )
        if not repo:
            return []

        runs = db.scalars(
            select(AnalysisRun)
            .where(AnalysisRun.repository_id == repository_id)
            .order_by(AnalysisRun.created_at.desc())
        ).all()

        return [AnalysisRunResponse.model_validate(r) for r in runs]

    @staticmethod
    def persist_scan_result(
        db: Session, run_id: str, scan_result: NormalizedScanResult
    ) -> AnalysisRun:
        run = db.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id))
        if not run:
            raise ValueError(f"AnalysisRun with id {run_id} not found")

        run.duration_ms = scan_result.duration_ms
        run.summary = scan_result.summary
        run.tool_version = scan_result.tool_version
        run.model_id = scan_result.model_id
        run.merge_base_sha = scan_result.merge_base_sha
        run.completed_at = datetime.now(timezone.utc)

        if not scan_result.success:
            run.status = "failed"
            run.error_message = scan_result.error_message
            db.commit()
            db.refresh(run)
            return run

        run.status = "completed"

        # Persist findings and evidence
        for nf in scan_result.findings:
            finding = Finding(
                analysis_run_id=run.id,
                finding_external_id=nf.external_id,
                status=nf.status,
                resolution_status="open",
                severity=nf.severity,
                rule_id=nf.rule_id,
                category=nf.category,
                title=nf.title,
                explanation=nf.explanation,
                confidence=nf.confidence,
                verification=nf.verification,
                suggested_action=nf.suggested_action,
            )
            db.add(finding)
            db.flush()  # assign finding.id

            for nev in nf.evidence:
                ev = Evidence(
                    finding_id=finding.id,
                    evidence_external_id=nev.external_id,
                    role=nev.role,
                    path=nev.path,
                    line_start=nev.line_start,
                    line_end=nev.line_end,
                    quote=nev.quote,
                    source_kind=nev.source_kind,
                    metadata_json=nev.metadata_json,
                )
                db.add(ev)

        db.commit()
        db.refresh(run)
        return run

    @staticmethod
    def run_analysis_job(
        db: Session,
        run_id: str,
        repo_path: Path,
        base_sha: str,
        head_sha: str,
        no_model: bool = False,
    ) -> AnalysisRun:
        run = db.scalar(select(AnalysisRun).where(AnalysisRun.id == run_id))
        if not run:
            raise ValueError(f"AnalysisRun with id {run_id} not found")

        run.status = "processing"
        run.started_at = datetime.now(timezone.utc)
        db.commit()

        adapter = DocSentryEngineAdapter()
        scan_result = adapter.execute_scan(
            repo_path=repo_path,
            base_sha=base_sha,
            head_sha=head_sha,
            no_model=no_model,
        )

        return AnalysisService.persist_scan_result(db, run_id, scan_result)
