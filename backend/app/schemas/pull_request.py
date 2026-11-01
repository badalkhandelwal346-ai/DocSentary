from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AnalysisSummaryBrief(BaseModel):
    id: str
    status: str
    drift_count: int = 0
    potential_drift_count: int = 0
    duration_ms: int = 0
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PullRequestResponse(BaseModel):
    id: str
    repository_id: str
    pr_number: int
    title: str
    state: str
    author_username: str
    base_ref: str
    base_sha: str
    head_ref: str
    head_sha: str
    html_url: str
    latest_analysis: Optional[AnalysisSummaryBrief] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PullRequestAnalyzeRequest(BaseModel):
    no_model: bool = False
    force_rescan: bool = False
