from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class OrganizationBase(BaseModel):
    name: str
    slug: str
    avatar_url: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationResponse(OrganizationBase):
    id: str
    role: Optional[str] = "member"
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    id: str
    action: str
    entity_type: str
    entity_id: str
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
    username: Optional[str] = None

    model_config = {"from_attributes": True}


class OrganizationActivityResponse(BaseModel):
    items: List[AuditLogResponse]
    total: int
