from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.dependencies import get_current_tenant_org
from backend.app.db.models.organization import Organization
from backend.app.db.models.pull_request import PullRequest
from backend.app.db.models.repository import Repository
from backend.app.db.session import SessionLocal, get_db
from backend.app.schemas.analysis import AnalysisRunQueueResponse
from backend.app.schemas.pull_request import PullRequestAnalyzeRequest, PullRequestResponse
from backend.app.services.analysis_service import AnalysisService
from backend.app.services.pull_request_service import PullRequestService

router = APIRouter(prefix="/pull-requests", tags=["Pull Requests"])


def _background_analysis_task(
    run_id: str,
    repo_path_str: str,
    base_sha: str,
    head_sha: str,
    no_model: bool,
):
    """
    Background worker thread function for asynchronous drift analysis.
    """
    db = SessionLocal()
    try:
        repo_path = Path(repo_path_str)
        AnalysisService.run_analysis_job(
            db=db,
            run_id=run_id,
            repo_path=repo_path,
            base_sha=base_sha,
            head_sha=head_sha,
            no_model=no_model,
        )
    finally:
        db.close()


@router.get("/{id}", response_model=PullRequestResponse)
def get_pull_request(
    id: str,
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> PullRequestResponse:
    pr = PullRequestService.get_pull_request(db, tenant_org.id, id)
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")
    return pr


@router.post("/{id}/analyze", response_model=AnalysisRunQueueResponse, status_code=status.HTTP_202_ACCEPTED)
def trigger_pull_request_analysis(
    id: str,
    payload: PullRequestAnalyzeRequest,
    background_tasks: BackgroundTasks,
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> AnalysisRunQueueResponse:
    pr = db.scalar(
        select(PullRequest)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .where(
            PullRequest.id == id,
            Repository.organization_id == tenant_org.id,
        )
    )
    if not pr:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")

    repo = db.scalar(select(Repository).where(Repository.id == pr.repository_id))
    if not repo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")

    # Enqueue AnalysisRun
    run = AnalysisService.create_analysis_run(
        db=db,
        organization_id=tenant_org.id,
        repository_id=repo.id,
        pull_request_id=pr.id,
        trigger_type="manual_api",
        base_sha=pr.base_sha,
        head_sha=pr.head_sha,
    )

    # Determine local repository path
    # If the repository is the current project workspace, use its path
    repo_path = Path(".").resolve()

    # Dispatch to background task runner
    background_tasks.add_task(
        _background_analysis_task,
        run.id,
        str(repo_path),
        pr.base_sha,
        pr.head_sha,
        payload.no_model,
    )

    return AnalysisRunQueueResponse(
        analysis_run_id=run.id,
        status="queued",
        message=f"Analysis successfully queued for PR #{pr.pr_number} ({pr.head_sha[:8]})",
    )
