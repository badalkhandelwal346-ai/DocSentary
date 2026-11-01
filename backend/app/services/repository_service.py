from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.models.analysis_run import AnalysisRun
from backend.app.db.models.finding import Finding
from backend.app.db.models.pull_request import PullRequest
from backend.app.db.models.repository import Repository
from backend.app.schemas.repository import RepositoryCreate, RepositoryResponse, RepositoryUpdate


class RepositoryService:
    @staticmethod
    def list_repositories(db: Session, organization_id: str) -> List[RepositoryResponse]:
        repos = db.scalars(
            select(Repository)
            .where(Repository.organization_id == organization_id)
            .order_by(Repository.created_at.desc())
        ).all()

        responses: List[RepositoryResponse] = []
        for r in repos:
            # Aggregate stats
            active_prs_count = db.scalar(
                select(func.count(PullRequest.id)).where(
                    PullRequest.repository_id == r.id, PullRequest.state == "open"
                )
            ) or 0

            open_findings_count = db.scalar(
                select(func.count(Finding.id))
                .join(AnalysisRun, Finding.analysis_run_id == AnalysisRun.id)
                .where(
                    AnalysisRun.repository_id == r.id,
                    Finding.status.in_(["DRIFT", "POTENTIAL_DRIFT"]),
                    Finding.resolution_status == "open",
                )
            ) or 0

            latest_analysis = db.scalar(
                select(AnalysisRun.created_at)
                .where(AnalysisRun.repository_id == r.id)
                .order_by(AnalysisRun.created_at.desc())
                .limit(1)
            )

            responses.append(
                RepositoryResponse(
                    id=r.id,
                    organization_id=r.organization_id,
                    github_repo_id=r.github_repo_id,
                    full_name=r.full_name,
                    default_branch=r.default_branch,
                    is_private=r.is_private,
                    clone_url=r.clone_url,
                    is_active=r.is_active,
                    config_override=r.config_override,
                    open_findings_count=open_findings_count,
                    active_prs_count=active_prs_count,
                    last_analysis_at=latest_analysis,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                )
            )
        return responses

    @staticmethod
    def get_repository(db: Session, organization_id: str, repo_id: str) -> Optional[Repository]:
        return db.scalar(
            select(Repository).where(
                Repository.id == repo_id,
                Repository.organization_id == organization_id,
            )
        )

    @staticmethod
    def create_repository(db: Session, organization_id: str, data: RepositoryCreate) -> Repository:
        existing = db.scalar(
            select(Repository).where(
                (Repository.full_name == data.full_name)
                | (
                    (Repository.github_repo_id == data.github_repo_id)
                    if data.github_repo_id
                    else False
                )
            )
        )
        if existing:
            return existing

        github_repo_id = data.github_repo_id or abs(hash(data.full_name)) % 100000000
        repo = Repository(
            organization_id=organization_id,
            github_repo_id=github_repo_id,
            full_name=data.full_name,
            default_branch=data.default_branch,
            is_private=data.is_private,
            clone_url=data.clone_url,
            is_active=data.is_active,
            config_override=data.config_override,
        )
        db.add(repo)
        db.commit()
        db.refresh(repo)
        return repo

    @staticmethod
    def update_repository(
        db: Session, organization_id: str, repo_id: str, data: RepositoryUpdate
    ) -> Optional[Repository]:
        repo = RepositoryService.get_repository(db, organization_id, repo_id)
        if not repo:
            return None

        if data.default_branch is not None:
            repo.default_branch = data.default_branch
        if data.is_active is not None:
            repo.is_active = data.is_active
        if data.config_override is not None:
            repo.config_override = data.config_override

        db.commit()
        db.refresh(repo)
        return repo

    @staticmethod
    def delete_repository(db: Session, organization_id: str, repo_id: str) -> bool:
        repo = RepositoryService.get_repository(db, organization_id, repo_id)
        if not repo:
            return False
        db.delete(repo)
        db.commit()
        return True
