from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import logging
from config.settings import settings

logger = logging.getLogger("ingestion-service")

VECTOR_SIZE = 1536


class QdrantStore:
    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self.collection = settings.qdrant_collection

    def ensure_collection(self):
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=VECTOR_SIZE,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Collection '{self.collection}' created")

    def upsert(self, chunks_with_embeddings: list[dict]):
        points = [
            PointStruct(
                id=c["id"],
                vector=c["embedding"],
                payload={"text": c["text"], **c["metadata"]},
            )
            for c in chunks_with_embeddings
        ]
        self.client.upsert(collection_name=self.collection, points=points)
        logger.info(f"Upserted {len(points)} points into '{self.collection}'")

    def is_healthy(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False