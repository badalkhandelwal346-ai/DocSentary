import logging
from typing import List, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_tenant_org, get_current_user
from backend.app.db.models.organization import Organization
from backend.app.db.models.pull_request import PullRequest
from backend.app.db.models.repository import Repository
from backend.app.db.models.user import User
from backend.app.db.session import get_db
from backend.app.schemas.auth import GitHubTokenConnectRequest

router = APIRouter(prefix="/github", tags=["GitHub Integration"])
logger = logging.getLogger(__name__)


class GitHubStatusResponse(BaseModel):
    is_connected: bool
    account_login: Optional[str] = None
    avatar_url: Optional[str] = None
    oauth_configured: bool
    webhook_configured: bool
    app_id_configured: bool


class DiscoveredRepository(BaseModel):
    github_repo_id: int
    full_name: str
    owner: str
    name: str
    description: Optional[str] = None
    default_branch: str
    is_private: bool
    clone_url: str
    html_url: str
    language: Optional[str] = None
    updated_at: Optional[str] = None
    is_connected: bool = False
    connected_id: Optional[str] = None


class DiscoveredPullRequest(BaseModel):
    pr_number: int
    title: str
    state: str
    author_username: str
    base_ref: str
    base_sha: str
    head_ref: str
    head_sha: str
    html_url: str
    created_at: str
    updated_at: str


@router.get("/status", response_model=GitHubStatusResponse)
def get_github_status(
    current_user: User = Depends(get_current_user),
) -> GitHubStatusResponse:
    has_token = bool(current_user.github_access_token)
    return GitHubStatusResponse(
        is_connected=has_token or bool(current_user.github_user_id),
        account_login=current_user.username if has_token else None,
        avatar_url=current_user.avatar_url,
        oauth_configured=bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET),
        webhook_configured=bool(settings.GITHUB_WEBHOOK_SECRET),
        app_id_configured=bool(settings.GITHUB_APP_ID),
    )


@router.post("/connect-token", response_model=GitHubStatusResponse)
def connect_github_token(
    payload: GitHubTokenConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GitHubStatusResponse:
    """
    Connect a GitHub token (OAuth token or Personal Access Token) to discover real repositories.
    """
    raw_token = payload.token.strip()
    try:
        resp = httpx.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {raw_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "DocSentry-App",
            },
            timeout=10.0,
        )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid GitHub token: GitHub rejected the credential.",
            )
        gh_user = resp.json()
        current_user.github_access_token = raw_token
        current_user.github_user_id = str(gh_user.get("id"))
        if not current_user.avatar_url:
            current_user.avatar_url = gh_user.get("avatar_url")
        db.commit()

        return GitHubStatusResponse(
            is_connected=True,
            account_login=gh_user.get("login"),
            avatar_url=gh_user.get("avatar_url"),
            oauth_configured=bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET),
            webhook_configured=bool(settings.GITHUB_WEBHOOK_SECRET),
            app_id_configured=bool(settings.GITHUB_APP_ID),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify GitHub token: {str(exc)}",
        ) from exc


@router.get("/repositories", response_model=List[DiscoveredRepository])
def discover_github_repositories(
    current_user: User = Depends(get_current_user),
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> List[DiscoveredRepository]:
    """
    Retrieves genuine GitHub repositories accessible to the user via GitHub API.
    """
    connected_repos = db.scalars(
        select(Repository).where(Repository.organization_id == tenant_org.id)
    ).all()
    connected_by_gh_id = {r.github_repo_id: r for r in connected_repos}
    connected_by_full_name = {r.full_name.lower(): r for r in connected_repos}

    # If user has GitHub token, query GitHub API
    if current_user.github_access_token:
        try:
            resp = httpx.get(
                "https://api.github.com/user/repos?per_page=100&sort=updated",
                headers={
                    "Authorization": f"Bearer {current_user.github_access_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "DocSentry-App",
                },
                timeout=12.0,
            )
            if resp.status_code == 200:
                raw_repos = resp.json()
                results: List[DiscoveredRepository] = []
                for r in raw_repos:
                    gh_id = r.get("id")
                    full_name = r.get("full_name")
                    matched = connected_by_gh_id.get(gh_id) or connected_by_full_name.get(full_name.lower())
                    results.append(
                        DiscoveredRepository(
                            github_repo_id=gh_id,
                            full_name=full_name,
                            owner=r.get("owner", {}).get("login", "unknown"),
                            name=r.get("name", full_name),
                            description=r.get("description"),
                            default_branch=r.get("default_branch", "main"),
                            is_private=r.get("private", False),
                            clone_url=r.get("clone_url", ""),
                            html_url=r.get("html_url", ""),
                            language=r.get("language"),
                            updated_at=r.get("updated_at"),
                            is_connected=matched is not None,
                            connected_id=matched.id if matched else None,
                        )
                    )
                return results
        except Exception as exc:
            logger.warning(f"Failed to fetch repositories from GitHub API: {exc}")

    # Fallback to connected repositories in database
    return [
        DiscoveredRepository(
            github_repo_id=r.github_repo_id,
            full_name=r.full_name,
            owner=r.full_name.split("/")[0] if "/" in r.full_name else "user",
            name=r.full_name.split("/")[1] if "/" in r.full_name else r.full_name,
            default_branch=r.default_branch,
            is_private=r.is_private,
            clone_url=r.clone_url,
            html_url=r.clone_url.replace(".git", ""),
            is_connected=True,
            connected_id=r.id,
        )
        for r in connected_repos
    ]


@router.get("/repositories/{owner}/{repo}/pull-requests", response_model=List[DiscoveredPullRequest])
def discover_github_pull_requests(
    owner: str,
    repo: str,
    current_user: User = Depends(get_current_user),
    tenant_org: Organization = Depends(get_current_tenant_org),
    db: Session = Depends(get_db),
) -> List[DiscoveredPullRequest]:
    """
    Fetches real pull requests directly from GitHub API for the specified repository.
    """
    full_name = f"{owner}/{repo}".lower()

    if current_user.github_access_token:
        try:
            resp = httpx.get(
                f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page=30",
                headers={
                    "Authorization": f"Bearer {current_user.github_access_token}",
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "DocSentry-App",
                },
                timeout=12.0,
            )
            if resp.status_code == 200:
                raw_prs = resp.json()
                results: List[DiscoveredPullRequest] = []
                for p in raw_prs:
                    results.append(
                        DiscoveredPullRequest(
                            pr_number=p.get("number"),
                            title=p.get("title", ""),
                            state=p.get("state", "open"),
                            author_username=p.get("user", {}).get("login", "unknown"),
                            base_ref=p.get("base", {}).get("ref", "main"),
                            base_sha=p.get("base", {}).get("sha", ""),
                            head_ref=p.get("head", {}).get("ref", ""),
                            head_sha=p.get("head", {}).get("sha", ""),
                            html_url=p.get("html_url", ""),
                            created_at=p.get("created_at", ""),
                            updated_at=p.get("updated_at", ""),
                        )
                    )
                return results
        except Exception as exc:
            logger.warning(f"Failed to fetch PRs from GitHub API for {full_name}: {exc}")

    # Fallback to database pull requests if already tracked
    r = db.scalar(
        select(Repository).where(
            Repository.organization_id == tenant_org.id,
            Repository.full_name.ilike(f"{owner}/{repo}"),
        )
    )
    if not r:
        return []

    prs = db.scalars(select(PullRequest).where(PullRequest.repository_id == r.id)).all()
    return [
        DiscoveredPullRequest(
            pr_number=p.pr_number,
            title=p.title,
            state=p.state,
            author_username=p.author_username,
            base_ref=p.base_ref,
            base_sha=p.base_sha,
            head_ref=p.head_ref,
            head_sha=p.head_sha,
            html_url=p.html_url,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )
        for p in prs
    ]
