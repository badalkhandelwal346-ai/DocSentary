from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WebhookEventResponse(BaseModel):
    id: str
    event_id: str
    event_type: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class WebhookReceiptResponse(BaseModel):
    status: str = "accepted"
    event_id: str
    message: str = "Webhook received and enqueued"
