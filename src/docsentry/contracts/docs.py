from typing import Literal

from pydantic import BaseModel, Field


class DocSpan(BaseModel):
    span_id: str
    path: str
    block_type: Literal["heading", "paragraph", "list_item", "table_cell", "fence"]
    heading_path: list[str] = Field(default_factory=list)
    text: str
    raw_text: str
    line_start: int  # 1-based inclusive
    line_end: int  # 1-based inclusive
    inline_code: list[str] = Field(default_factory=list)
    links: list[str] = Field(default_factory=list)
    language: str | None = None
    claim_type: Literal[
        "active_assertion",
        "procedural_instruction",
        "api_reference",
        "configuration_instruction",
        "code_example",
        "historical_migration",
        "version_specific",
        "general_description",
    ] = "active_assertion"


class CandidateLink(BaseModel):
    code_fact_id: str
    doc_span_id: str
    score: float
    match_reasons: list[str]
    rank: int
