from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_tenant_org, get_current_user
from backend.app.db.models.organization import Organization
from backend.app.db.models.user import User
from backend.app.db.session import get_db
from backend.app.schemas.finding import FindingResponse, FindingStatusUpdateRequest
from backend.app.services.finding_service import FindingService

router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("/{id}", response_model=FindingResponse)
def get_finding(
    id: str,
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> FindingResponse:
    finding = FindingService.get_finding(db, tenant_org.id, id)
    if not finding:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return finding


@router.patch("/{id}/status", response_model=FindingResponse)
def update_finding_status(
    id: str,
    payload: FindingStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> FindingResponse:
    updated = FindingService.update_finding_status(
        db=db,
        organization_id=tenant_org.id,
        finding_id=id,
        user_id=current_user.id,
        resolution_status=payload.resolution_status,
        resolution_reason=payload.resolution_reason,
    )
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Finding not found")
    return updated
