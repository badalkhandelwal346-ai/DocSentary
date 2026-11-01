import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.db.models.finding import Finding
    from backend.app.db.models.organization import Organization
    from backend.app.db.models.pull_request import PullRequest
    from backend.app.db.models.repository import Repository


class AnalysisRun(Base, TimestampMixin):
    __tablename__ = "analysis_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False
    )
    repository_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("repositories.id", ondelete="CASCADE"), index=True, nullable=False
    )
    pull_request_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("pull_requests.id", ondelete="CASCADE"), index=True, nullable=True
    )

    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)  # webhook_pr_sync, manual, cli, etc.
    status: Mapped[str] = mapped_column(String(50), default="queued", index=True, nullable=False)  # queued, processing, completed, failed, cancelled

    base_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    head_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    merge_base_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    tool_version: Mapped[str] = mapped_column(String(50), default="0.2.0", nullable=False)
    model_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="analysis_runs")
    repository: Mapped["Repository"] = relationship("Repository", back_populates="analysis_runs")
    pull_request: Mapped[Optional["PullRequest"]] = relationship("PullRequest", back_populates="analysis_runs")
    findings: Mapped[List["Finding"]] = relationship(
        "Finding", back_populates="analysis_run", cascade="all, delete-orphan"
    )
