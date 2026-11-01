from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_tenant_org
from backend.app.db.models.organization import Organization
from backend.app.db.session import get_db
from backend.app.schemas.analysis import AnalysisRunResponse
from backend.app.schemas.pull_request import PullRequestResponse
from backend.app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryUpdate
from backend.app.services.analysis_service import AnalysisService
from backend.app.services.pull_request_service import PullRequestService
from backend.app.services.repository_service import RepositoryService

router = APIRouter(prefix="/repositories", tags=["Repositories"])


@router.get("", response_model=List[RepositoryResponse])
def list_repositories(
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> List[RepositoryResponse]:
    return RepositoryService.list_repositories(db, tenant_org.id)


@router.post("", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
def create_repository(
    payload: RepositoryCreate,
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> RepositoryResponse:
    repo = RepositoryService.create_repository(db, tenant_org.id, payload)
    return RepositoryResponse.model_validate(repo)


@router.get("/{id}", response_model=RepositoryResponse)
def get_repository(
    id: str,
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> RepositoryResponse:
    repo = RepositoryService.get_repository(db, tenant_org.id, id)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return RepositoryResponse.model_validate(repo)


@router.patch("/{id}", response_model=RepositoryResponse)
def update_repository(
    id: str,
    payload: RepositoryUpdate,
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> RepositoryResponse:
    repo = RepositoryService.update_repository(db, tenant_org.id, id, payload)
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return RepositoryResponse.model_validate(repo)


@router.delete("/{id}")
def delete_repository(
    id: str,
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> dict:
    success = RepositoryService.delete_repository(db, tenant_org.id, id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
    return {"status": "deleted", "id": id}


@router.get("/{id}/pull-requests", response_model=List[PullRequestResponse])
def list_repository_pull_requests(
    id: str,
    state: Optional[str] = Query(None, description="Filter by state: open, closed, all"),
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> List[PullRequestResponse]:
    return PullRequestService.list_pull_requests(db, tenant_org.id, id, state=state)


@router.get("/{id}/analyses", response_model=List[AnalysisRunResponse])
def list_repository_analyses(
    id: str,
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> List[AnalysisRunResponse]:
    return AnalysisService.list_analyses_for_repo(db, tenant_org.id, id)
