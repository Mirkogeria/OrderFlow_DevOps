from fastapi import FastAPI, UploadFile, File, HTTPException
import logging
from config.settings import settings
from pipeline.orchestrator import IngestionOrchestrator
from pipeline.qdrant_store import QdrantStore
from models.document import IngestResponse, HealthResponse

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ingestion-service")

app = FastAPI(
    title="OrderFlow - Ingestion Service",
    description="Carica e indicizza documenti tecnici per il chatbot RAG",
    version="1.0.0"
)

orchestrator = IngestionOrchestrator()
store = QdrantStore()


@app.get("/health", response_model=HealthResponse)
def health_check():
    return HealthResponse(
        status="healthy",
        service="ingestion-service",
        version="1.0.0",
        environment=settings.environment,
        qdrant_connected=store.is_healthy(),
    )


@app.post("/api/ingest", response_model=IngestResponse, status_code=201)
async def ingest_document(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo file PDF supportati")
    file_bytes = await file.read()
    try:
        result = orchestrator.ingest_file(
            source=file.filename,
            file_bytes=file_bytes
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return result


@app.get("/api/collections")
def list_collections():
    try:
        collections = store.client.get_collections().collections
        return {"collections": [c.name for c in collections]}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Qdrant non raggiungibile: {e}")