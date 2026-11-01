from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from backend.app.schemas.finding import FindingResponse


class AnalysisRunResponse(BaseModel):
    id: str
    organization_id: str
    repository_id: str
    pull_request_id: Optional[str] = None
    trigger_type: str
    status: str
    base_sha: str
    head_sha: str
    merge_base_sha: str
    tool_version: str
    model_id: Optional[str] = None
    duration_ms: int = 0
    summary: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AnalysisRunDetailResponse(AnalysisRunResponse):
    findings: List[FindingResponse] = []


class AnalysisRunQueueResponse(BaseModel):
    analysis_run_id: str
    status: str
    message: str
