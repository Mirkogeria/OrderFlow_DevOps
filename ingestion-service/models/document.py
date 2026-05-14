from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentChunk(BaseModel):
    id: str
    text: str
    embedding: Optional[list[float]] = None
    metadata: dict = {}
    created_at: str = datetime.utcnow().isoformat()


class IngestRequest(BaseModel):
    source: str
    content_type: str = "pdf"


class IngestResponse(BaseModel):
    source: str
    chunks_created: int
    collection: str
    status: str = "completed"


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    qdrant_connected: bool