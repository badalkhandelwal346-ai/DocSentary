from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models.analysis_run import AnalysisRun
from backend.app.db.models.finding import Finding
from backend.app.db.models.pull_request import PullRequest
from backend.app.db.models.repository import Repository
from backend.app.schemas.pull_request import AnalysisSummaryBrief, PullRequestResponse


class PullRequestService:
    @staticmethod
    def list_pull_requests(
        db: Session, organization_id: str, repository_id: str, state: Optional[str] = None
    ) -> List[PullRequestResponse]:
        # Validate repo belongs to org
        repo = db.scalar(
            select(Repository).where(
                Repository.id == repository_id,
                Repository.organization_id == organization_id,
            )
        )
        if not repo:
            return []

        query = select(PullRequest).where(PullRequest.repository_id == repository_id)
        if state and state != "all":
            query = query.where(PullRequest.state == state)

        prs = db.scalars(query.order_by(PullRequest.created_at.desc())).all()

        results: List[PullRequestResponse] = []
        for pr in prs:
            # Fetch latest analysis
            latest_run = db.scalar(
                select(AnalysisRun)
                .where(AnalysisRun.pull_request_id == pr.id)
                .order_by(AnalysisRun.created_at.desc())
                .limit(1)
            )

            latest_brief = None
            if latest_run:
                drift_count = db.scalar(
                    select(Finding.id)
                    .where(
                        Finding.analysis_run_id == latest_run.id,
                        Finding.status == "DRIFT",
                    )
                ) is not None

                latest_brief = AnalysisSummaryBrief(
                    id=latest_run.id,
                    status=latest_run.status,
                    drift_count=1 if drift_count else 0,
                    potential_drift_count=0,
                    duration_ms=latest_run.duration_ms,
                    completed_at=latest_run.completed_at,
                )

            results.append(
                PullRequestResponse(
                    id=pr.id,
                    repository_id=pr.repository_id,
                    pr_number=pr.pr_number,
                    title=pr.title,
                    state=pr.state,
                    author_username=pr.author_username,
                    base_ref=pr.base_ref,
                    base_sha=pr.base_sha,
                    head_ref=pr.head_ref,
                    head_sha=pr.head_sha,
                    html_url=pr.html_url,
                    latest_analysis=latest_brief,
                    created_at=pr.created_at,
                    updated_at=pr.updated_at,
                )
            )
        return results

    @staticmethod
    def get_pull_request(
        db: Session, organization_id: str, pr_id: str
    ) -> Optional[PullRequestResponse]:
        pr = db.scalar(
            select(PullRequest)
            .join(Repository, PullRequest.repository_id == Repository.id)
            .where(
                PullRequest.id == pr_id,
                Repository.organization_id == organization_id,
            )
        )
        if not pr:
            return None

        latest_run = db.scalar(
            select(AnalysisRun)
            .where(AnalysisRun.pull_request_id == pr.id)
            .order_by(AnalysisRun.created_at.desc())
            .limit(1)
        )
        latest_brief = None
        if latest_run:
            latest_brief = AnalysisSummaryBrief(
                id=latest_run.id,
                status=latest_run.status,
                drift_count=latest_run.summary.get("drift", 0) if latest_run.summary else 0,
                potential_drift_count=(
                    latest_run.summary.get("potential_drift", 0) if latest_run.summary else 0
                ),
                duration_ms=latest_run.duration_ms,
                completed_at=latest_run.completed_at,
            )

        return PullRequestResponse(
            id=pr.id,
            repository_id=pr.repository_id,
            pr_number=pr.pr_number,
            title=pr.title,
            state=pr.state,
            author_username=pr.author_username,
            base_ref=pr.base_ref,
            base_sha=pr.base_sha,
            head_ref=pr.head_ref,
            head_sha=pr.head_sha,
            html_url=pr.html_url,
            latest_analysis=latest_brief,
            created_at=pr.created_at,
            updated_at=pr.updated_at,
        )

    @staticmethod
    def upsert_pull_request(
        db: Session,
        repository_id: str,
        pr_number: int,
        title: str,
        state: str,
        author_username: str,
        base_ref: str,
        base_sha: str,
        head_ref: str,
        head_sha: str,
        html_url: str,
    ) -> PullRequest:
        pr = db.scalar(
            select(PullRequest).where(
                PullRequest.repository_id == repository_id,
                PullRequest.pr_number == pr_number,
            )
        )
        if pr:
            pr.title = title
            pr.state = state
            pr.author_username = author_username
            pr.base_ref = base_ref
            pr.base_sha = base_sha
            pr.head_ref = head_ref
            pr.head_sha = head_sha
            pr.html_url = html_url
        else:
            pr = PullRequest(
                repository_id=repository_id,
                pr_number=pr_number,
                title=title,
                state=state,
                author_username=author_username,
                base_ref=base_ref,
                base_sha=base_sha,
                head_ref=head_ref,
                head_sha=head_sha,
                html_url=html_url,
            )
            db.add(pr)

        db.commit()
        db.refresh(pr)
        return pr
