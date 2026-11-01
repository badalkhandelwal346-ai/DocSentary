from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "0.2.0"
    database: str = "connected"
    worker_queue: str = "idle"
    environment: str = "development"
