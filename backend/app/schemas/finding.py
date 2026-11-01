from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class EvidenceResponse(BaseModel):
    id: str
    evidence_external_id: str
    role: Literal["code", "documentation"]
    path: str
    line_start: int
    line_end: int
    quote: str
    source_kind: Literal["ast_fact", "diff_hunk", "doc_span"]
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FindingResponse(BaseModel):
    id: str
    analysis_run_id: str
    finding_external_id: str
    status: Literal["DRIFT", "POTENTIAL_DRIFT", "NO_DRIFT", "UNCERTAIN"]
    resolution_status: Literal["open", "acknowledged", "dismissed", "resolved"]
    resolution_reason: Optional[str] = None
    resolved_by_user_id: Optional[str] = None
    resolved_at: Optional[datetime] = None
    severity: Literal["critical", "high", "medium", "low", "info"]
    rule_id: str
    category: str
    title: str
    explanation: str
    confidence: Optional[float] = None
    verification: Literal["deterministic", "model_assisted", "human_fixture"]
    suggested_action: Optional[str] = None
    evidence: List[EvidenceResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class FindingStatusUpdateRequest(BaseModel):
    resolution_status: Literal["open", "acknowledged", "dismissed", "resolved"]
    resolution_reason: Optional[str] = None


FindingDetailResponse = FindingResponse
