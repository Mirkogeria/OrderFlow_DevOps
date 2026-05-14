from pydantic import BaseModel
from typing import Optional


class ChatMessage(BaseModel):
    """Singolo messaggio nella conversazione."""
    role: str        # "user" o "assistant"
    content: str


class ChatRequest(BaseModel):
    """Richiesta al chatbot."""
    question: str
    session_id: Optional[str] = "default"
    stream: bool = False


class ChatResponse(BaseModel):
    """Risposta del chatbot."""
    answer: str
    session_id: str
    sources: list[str] = []
    model: str


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    qdrant_connected: bool
    bedrock_available: bool