from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class EvaluationRunResponse(BaseModel):
    id: str
    benchmark_name: str
    dataset_type: str
    total_cases: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    metrics_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class EvaluationListResponse(BaseModel):
    items: List[EvaluationRunResponse]
    total: int
