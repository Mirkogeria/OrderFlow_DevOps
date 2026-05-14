from fastapi import FastAPI
import logging
from config.settings import settings
from api.routes import router
from api.streaming import stream_chat
from models.chat_models import ChatRequest, HealthResponse
from retriever.qdrant_retriever import QdrantRetriever
import boto3

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("genai-service")

app = FastAPI(
    title="OrderFlow - GenAI Service",
    description="Chatbot RAG su documentazione tecnica con Claude su Amazon Bedrock",
    version="1.0.0"
)

app.include_router(router, prefix="/api")


@app.get("/health", response_model=HealthResponse)
def health_check():
    retriever = QdrantRetriever()
    bedrock_ok = True
    try:
        boto3.client("bedrock-runtime", region_name=settings.aws_region)
    except Exception:
        bedrock_ok = False

    return HealthResponse(
        status="healthy",
        service="genai-service",
        version="1.0.0",
        environment=settings.environment,
        qdrant_connected=retriever.is_healthy(),
        bedrock_available=bedrock_ok,
    )


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Endpoint streaming: restituisce la risposta token per token."""
    return stream_chat(
        question=request.question,
        session_id=request.session_id,
    )