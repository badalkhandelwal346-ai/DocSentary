import logging
from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models.analysis_run import AnalysisRun
from backend.app.db.models.github_installation import GitHubInstallation
from backend.app.db.models.organization import Organization
from backend.app.db.models.repository import Repository
from backend.app.db.models.webhook_event import WebhookEvent
from backend.app.services.pull_request_service import PullRequestService

logger = logging.getLogger(__name__)


class GitHubService:
    @staticmethod
    def record_and_verify_webhook(
        db: Session,
        delivery_id: str,
        event_type: str,
        signature: str,
        payload: Dict[str, Any],
    ) -> Tuple[WebhookEvent, bool]:
        """
        Records inbound webhook delivery and checks for idempotency deduplication.
        Returns (WebhookEvent, is_new).
        """
        existing = db.scalar(select(WebhookEvent).where(WebhookEvent.event_id == delivery_id))
        if existing:
            return existing, False

        event = WebhookEvent(
            event_id=delivery_id,
            event_type=event_type,
            signature=signature,
            payload=payload,
            status="received",
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event, True

    @staticmethod
    def process_webhook_event(db: Session, event_id: str) -> WebhookEvent:
        """
        Processes a received webhook event according to GitHub App specifications.
        """
        event = db.scalar(select(WebhookEvent).where(WebhookEvent.event_id == event_id))
        if not event:
            raise ValueError(f"WebhookEvent with delivery ID {event_id} not found")

        payload = event.payload
        event_type = event.event_type

        try:
            if event_type == "ping":
                event.status = "processed"
                event.processed_at = datetime.now(timezone.utc)
                db.commit()
                return event

            elif event_type == "installation":
                action = payload.get("action")
                installation_data = payload.get("installation", {})
                inst_id = installation_data.get("id")
                account = installation_data.get("account", {})
                account_login = account.get("login", "unknown")
                account_type = account.get("type", "User")

                if inst_id and action in ["created", "unsuspend"]:
                    # Find or associate organization
                    org = db.scalar(
                        select(Organization).where(Organization.slug == account_login.lower())
                    )
                    if not org:
                        # Auto-create or pick default org
                        org = db.scalar(select(Organization).limit(1))
                    if org:
                        inst = db.scalar(
                            select(GitHubInstallation).where(
                                GitHubInstallation.github_installation_id == inst_id
                            )
                        )
                        if not inst:
                            inst = GitHubInstallation(
                                github_installation_id=inst_id,
                                organization_id=org.id,
                                account_login=account_login,
                                account_type=account_type,
                                permissions=installation_data.get("permissions"),
                            )
                            db.add(inst)
                        else:
                            inst.account_login = account_login
                            inst.permissions = installation_data.get("permissions")
                        db.commit()

                event.status = "processed"
                event.processed_at = datetime.now(timezone.utc)
                db.commit()
                return event

            elif event_type == "pull_request":
                action = payload.get("action")
                pr_data = payload.get("pull_request", {})
                repo_data = payload.get("repository", {})
                github_repo_id = repo_data.get("id")
                full_name = repo_data.get("full_name")

                repo = None
                if github_repo_id:
                    repo = db.scalar(
                        select(Repository).where(Repository.github_repo_id == github_repo_id)
                    )
                if not repo and full_name:
                    repo = db.scalar(select(Repository).where(Repository.full_name == full_name))

                if not repo:
                    # Repository not registered yet in DocSentry
                    event.status = "ignored"
                    event.error_message = f"Repository {full_name} is not registered in DocSentry"
                    event.processed_at = datetime.now(timezone.utc)
                    db.commit()
                    return event

                pr_number = pr_data.get("number")
                title = pr_data.get("title", f"PR #{pr_number}")
                author = pr_data.get("user", {}).get("login", "unknown")
                base_ref = pr_data.get("base", {}).get("ref", "main")
                base_sha = pr_data.get("base", {}).get("sha", "")
                head_ref = pr_data.get("head", {}).get("ref", "")
                head_sha = pr_data.get("head", {}).get("sha", "")
                html_url = pr_data.get("html_url", "")
                pr_state = "closed" if action == "closed" else "open"

                pr = PullRequestService.upsert_pull_request(
                    db=db,
                    repository_id=repo.id,
                    pr_number=pr_number,
                    title=title,
                    state=pr_state,
                    author_username=author,
                    base_ref=base_ref,
                    base_sha=base_sha,
                    head_ref=head_ref,
                    head_sha=head_sha,
                    html_url=html_url,
                )

                if action in ["opened", "synchronize", "reopened"]:
                    # Create queued AnalysisRun
                    run = AnalysisRun(
                        organization_id=repo.organization_id,
                        repository_id=repo.id,
                        pull_request_id=pr.id,
                        trigger_type=f"webhook_pr_{action}",
                        status="queued",
                        base_sha=base_sha,
                        head_sha=head_sha,
                        merge_base_sha=base_sha,
                        tool_version="0.2.0",
                    )
                    db.add(run)
                    db.commit()

                event.status = "processed"
                event.processed_at = datetime.now(timezone.utc)
                db.commit()
                return event

            else:
                event.status = "ignored"
                event.error_message = f"Unhandled event type: {event_type}"
                event.processed_at = datetime.now(timezone.utc)
                db.commit()
                return event

        except Exception as exc:
            logger.exception(f"Error processing webhook event {event_id}: {exc}")
            event.status = "failed"
            event.error_message = str(exc)
            event.processed_at = datetime.now(timezone.utc)
            db.commit()
            return event
