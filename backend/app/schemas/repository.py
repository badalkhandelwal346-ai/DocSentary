from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class RepositoryBase(BaseModel):
    full_name: str
    default_branch: str = "main"
    clone_url: str
    is_private: bool = False
    is_active: bool = True
    config_override: Optional[Dict[str, Any]] = None


class RepositoryCreate(RepositoryBase):
    github_repo_id: Optional[int] = None


class RepositoryUpdate(BaseModel):
    default_branch: Optional[str] = None
    is_active: Optional[bool] = None
    config_override: Optional[Dict[str, Any]] = None


class RepositoryResponse(RepositoryBase):
    id: str
    organization_id: str
    github_repo_id: int
    open_findings_count: int = 0
    active_prs_count: int = 0
    last_analysis_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
