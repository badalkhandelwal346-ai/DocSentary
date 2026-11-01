from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.app.db.models.analysis_run import AnalysisRun
from backend.app.db.models.audit_log import AuditLog
from backend.app.db.models.finding import Finding
from backend.app.schemas.finding import EvidenceResponse, FindingResponse


class FindingService:
    @staticmethod
    def _to_schema(f: Finding) -> FindingResponse:
        evidence_list = [
            EvidenceResponse(
                id=ev.id,
                evidence_external_id=ev.evidence_external_id,
                role=ev.role,  # type: ignore
                path=ev.path,
                line_start=ev.line_start,
                line_end=ev.line_end,
                quote=ev.quote,
                source_kind=ev.source_kind,  # type: ignore
                metadata_json=ev.metadata_json,
                created_at=ev.created_at,
            )
            for ev in f.evidence
        ]

        return FindingResponse(
            id=f.id,
            analysis_run_id=f.analysis_run_id,
            finding_external_id=f.finding_external_id,
            status=f.status,  # type: ignore
            resolution_status=f.resolution_status,  # type: ignore
            resolution_reason=f.resolution_reason,
            resolved_by_user_id=f.resolved_by_user_id,
            resolved_at=f.resolved_at,
            severity=f.severity,  # type: ignore
            rule_id=f.rule_id,
            category=f.category,
            title=f.title,
            explanation=f.explanation,
            confidence=f.confidence,
            verification=f.verification,  # type: ignore
            suggested_action=f.suggested_action,
            evidence=evidence_list,
            created_at=f.created_at,
        )

    @staticmethod
    def get_finding(
        db: Session, organization_id: str, finding_id: str
    ) -> Optional[FindingResponse]:
        f = db.scalar(
            select(Finding)
            .options(selectinload(Finding.evidence))
            .join(AnalysisRun, Finding.analysis_run_id == AnalysisRun.id)
            .where(
                Finding.id == finding_id,
                AnalysisRun.organization_id == organization_id,
            )
        )
        if not f:
            return None
        return FindingService._to_schema(f)

    @staticmethod
    def list_findings_for_analysis(
        db: Session, organization_id: str, analysis_id: str
    ) -> List[FindingResponse]:
        run = db.scalar(
            select(AnalysisRun).where(
                AnalysisRun.id == analysis_id,
                AnalysisRun.organization_id == organization_id,
            )
        )
        if not run:
            return []

        findings = db.scalars(
            select(Finding)
            .options(selectinload(Finding.evidence))
            .where(Finding.analysis_run_id == analysis_id)
            .order_by(Finding.created_at.asc())
        ).all()

        return [FindingService._to_schema(f) for f in findings]

    @staticmethod
    def update_finding_status(
        db: Session,
        organization_id: str,
        finding_id: str,
        user_id: Optional[str],
        resolution_status: str,
        resolution_reason: Optional[str] = None,
    ) -> Optional[FindingResponse]:
        f = db.scalar(
            select(Finding)
            .options(selectinload(Finding.evidence))
            .join(AnalysisRun, Finding.analysis_run_id == AnalysisRun.id)
            .where(
                Finding.id == finding_id,
                AnalysisRun.organization_id == organization_id,
            )
        )
        if not f:
            return None

        old_status = f.resolution_status
        f.resolution_status = resolution_status
        f.resolution_reason = resolution_reason
        f.resolved_by_user_id = user_id
        f.resolved_at = datetime.now(timezone.utc)

        # Audit log
        audit = AuditLog(
            organization_id=organization_id,
            user_id=user_id,
            action="finding.status_updated",
            entity_type="finding",
            entity_id=f.id,
            details={
                "old_resolution_status": old_status,
                "new_resolution_status": resolution_status,
                "reason": resolution_reason,
            },
        )
        db.add(audit)
        db.commit()
        db.refresh(f)
        return FindingService._to_schema(f)
