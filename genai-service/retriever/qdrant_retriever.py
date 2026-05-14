import boto3
import json
import logging
from qdrant_client import QdrantClient
from config.settings import settings

logger = logging.getLogger("genai-service")


class QdrantRetriever:
    """Recupera i chunk più rilevanti da Qdrant dato un testo di query."""

    def __init__(self):
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        self.collection = settings.qdrant_collection
        self.top_k = settings.retriever_top_k
        self.bedrock = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
        )
        self.embedding_model = settings.bedrock_embedding_model

    def _embed_query(self, text: str) -> list[float]:
        """Genera embedding della query con Bedrock Titan."""
        body = json.dumps({"inputText": text})
        response = self.bedrock.invoke_model(
            modelId=self.embedding_model,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        result = json.loads(response["body"].read())
        return result["embedding"]

    def retrieve(self, query: str) -> list[dict]:
        """Restituisce i top_k chunk più simili alla query."""
        query_embedding = self._embed_query(query)
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            limit=self.top_k,
        )
        chunks = []
        for hit in results:
            chunks.append({
                "text": hit.payload.get("text", ""),
                "source": hit.payload.get("source", "unknown"),
                "page": hit.payload.get("page", 0),
                "score": hit.score,
            })
        logger.info(f"Retrieved {len(chunks)} chunks for query")
        return chunks

    def is_healthy(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False