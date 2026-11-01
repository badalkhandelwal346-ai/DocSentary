from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_user
from backend.app.db.models.audit_log import AuditLog
from backend.app.db.models.organization import Organization
from backend.app.db.models.organization_member import OrganizationMember
from backend.app.db.models.user import User
from backend.app.db.session import get_db
from backend.app.schemas.organization import (
    AuditLogResponse,
    OrganizationActivityResponse,
    OrganizationResponse,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


@router.get("", response_model=List[OrganizationResponse])
def list_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[OrganizationResponse]:
    memberships = db.scalars(
        select(OrganizationMember)
        .where(OrganizationMember.user_id == current_user.id)
    ).all()

    results: List[OrganizationResponse] = []
    for m in memberships:
        org = db.scalar(select(Organization).where(Organization.id == m.organization_id))
        if org:
            results.append(
                OrganizationResponse(
                    id=org.id,
                    slug=org.slug,
                    name=org.name,
                    avatar_url=org.avatar_url,
                    role=m.role,
                    created_at=org.created_at,
                )
            )
    return results


@router.get("/{id}", response_model=OrganizationResponse)
def get_organization(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationResponse:
    membership = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == id,
            OrganizationMember.user_id == current_user.id,
        )
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or access denied",
        )

    org = db.scalar(select(Organization).where(Organization.id == id))
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    return OrganizationResponse(
        id=org.id,
        slug=org.slug,
        name=org.name,
        avatar_url=org.avatar_url,
        role=membership.role,
        created_at=org.created_at,
    )


@router.get("/{id}/activity", response_model=OrganizationActivityResponse)
def get_organization_activity(
    id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OrganizationActivityResponse:
    membership = db.scalar(
        select(OrganizationMember).where(
            OrganizationMember.organization_id == id,
            OrganizationMember.user_id == current_user.id,
        )
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or access denied",
        )

    total = db.scalar(
        select(func.count(AuditLog.id)).where(AuditLog.organization_id == id)
    ) or 0

    logs = db.scalars(
        select(AuditLog)
        .where(AuditLog.organization_id == id)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    items: List[AuditLogResponse] = []
    for log in logs:
        username = None
        if log.user_id:
            u = db.scalar(select(User.username).where(User.id == log.user_id))
            username = u

        items.append(
            AuditLogResponse(
                id=log.id,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                details=log.details,
                created_at=log.created_at,
                username=username,
            )
        )

    return OrganizationActivityResponse(items=items, total=total)
