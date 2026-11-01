from typing import Literal

from pydantic import BaseModel, Field


class EvidenceItem(BaseModel):
    evidence_id: str
    role: Literal["code", "documentation"]
    path: str
    line_start: int
    line_end: int
    quote: str
    source_kind: Literal["ast_fact", "diff_hunk", "doc_span"]


class EvidenceBundle(BaseModel):
    bundle_id: str
    code_fact_id: str
    code_fact_summary: str
    code_path: str
    code_before: str | None = None
    code_after: str | None = None
    claim_type: str | None = None
    heading_context: str | None = None
    evidence_items: list[EvidenceItem] = Field(default_factory=list)


class ModelAssessment(BaseModel):
    status: Literal["DRIFT", "POTENTIAL_DRIFT", "NO_DRIFT", "UNCERTAIN"]
    severity: Literal["critical", "high", "medium", "low", "info"] = "medium"
    explanation: str
    evidence_ids: list[str] = Field(default_factory=list)
    claim_status: Literal[
        "contradicted",
        "partially_outdated",
        "incomplete_new_capability",
        "still_accurate",
        "historical",
        "uncertain",
    ] = "contradicted"
    reasoning_type: Literal[
        "direct_contradiction",
        "likely_outdated",
        "no_change",
        "insufficient_context",
    ] = "likely_outdated"
    suggested_action: str | None = None
