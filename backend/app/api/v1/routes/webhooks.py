import json
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import verify_github_signature
from backend.app.db.session import SessionLocal, get_db
from backend.app.schemas.webhook import WebhookReceiptResponse
from backend.app.services.github_service import GitHubService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


def _background_process_webhook(delivery_id: str):
    db = SessionLocal()
    try:
        GitHubService.process_webhook_event(db, delivery_id)
    finally:
        db.close()


@router.post("/github", response_model=WebhookReceiptResponse, status_code=status.HTTP_202_ACCEPTED)
async def receive_github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    db: Session = Depends(get_db),
) -> WebhookReceiptResponse:
    if not x_github_delivery:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required header: X-GitHub-Delivery",
        )
    if not x_github_event:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required header: X-GitHub-Event",
        )

    body_bytes = await request.body()

    # Signature verification (enforced whenever webhook secret is configured)
    if settings.GITHUB_WEBHOOK_SECRET:
        is_valid = verify_github_signature(
            payload_body=body_bytes,
            signature_header=x_hub_signature_256,
            secret=settings.GITHUB_WEBHOOK_SECRET,
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid X-Hub-Signature-256 HMAC signature",
            )

    try:
        payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Malformed JSON payload: {str(exc)}",
        ) from exc

    event, is_new = GitHubService.record_and_verify_webhook(
        db=db,
        delivery_id=x_github_delivery,
        event_type=x_github_event,
        signature=x_hub_signature_256 or "unsigned_dev",
        payload=payload,
    )

    if not is_new:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate webhook delivery {x_github_delivery} already processed",
        )

    # Dispatch to background task processing
    background_tasks.add_task(_background_process_webhook, x_github_delivery)

    return WebhookReceiptResponse(
        status="accepted",
        event_id=x_github_delivery,
        message=f"GitHub event '{x_github_event}' accepted and scheduled for processing",
    )
