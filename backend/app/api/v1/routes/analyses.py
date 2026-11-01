from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_tenant_org
from backend.app.db.models.organization import Organization
from backend.app.db.session import get_db
from backend.app.schemas.analysis import AnalysisRunResponse
from backend.app.schemas.finding import FindingResponse
from backend.app.services.analysis_service import AnalysisService
from backend.app.services.finding_service import FindingService

router = APIRouter(prefix="/analyses", tags=["Analyses"])


@router.get("/{id}", response_model=AnalysisRunResponse)
def get_analysis_run(
    id: str,
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> AnalysisRunResponse:
    run = AnalysisService.get_analysis_run(db, tenant_org.id, id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis run not found")
    return run


@router.get("/{id}/findings", response_model=List[FindingResponse])
def get_analysis_findings(
    id: str,
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> List[FindingResponse]:
    return FindingService.list_findings_for_analysis(db, tenant_org.id, id)
