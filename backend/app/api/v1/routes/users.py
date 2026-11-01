from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_tenant_org, get_current_user
from backend.app.db.models.organization import Organization
from backend.app.db.models.repository import Repository
from backend.app.db.models.user import User
from backend.app.db.session import get_db
from backend.app.schemas.auth import OnboardingStatus, OnboardingUpdateRequest

router = APIRouter(prefix="/users", tags=["Users & Onboarding"])


@router.get("/onboarding", response_model=OnboardingStatus)
def get_onboarding_status(
    current_user: User = Depends(get_current_user),
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> OnboardingStatus:
    repo_count = db.scalar(
        select(func.count(Repository.id)).where(Repository.organization_id == tenant_org.id)
    ) or 0

    return OnboardingStatus(
        onboarding_step=current_user.onboarding_step,
        onboarding_completed=current_user.onboarding_completed,
        has_github_connected=bool(current_user.github_access_token or current_user.github_user_id),
        connected_repos_count=repo_count,
    )


@router.patch("/onboarding", response_model=OnboardingStatus)
def update_onboarding_status(
    payload: OnboardingUpdateRequest,
    current_user: User = Depends(get_current_user),
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> OnboardingStatus:
    if payload.onboarding_step is not None:
        current_user.onboarding_step = payload.onboarding_step
    if payload.onboarding_completed is not None:
        current_user.onboarding_completed = payload.onboarding_completed

    db.commit()
    db.refresh(current_user)

    repo_count = db.scalar(
        select(func.count(Repository.id)).where(Repository.organization_id == tenant_org.id)
    ) or 0

    return OnboardingStatus(
        onboarding_step=current_user.onboarding_step,
        onboarding_completed=current_user.onboarding_completed,
        has_github_connected=bool(current_user.github_access_token or current_user.github_user_id),
        connected_repos_count=repo_count,
    )
