import logging
from loaders.pdf_loader import PdfLoader
from pipeline.chunker import Chunker
from pipeline.embedder import BedrockEmbedder
from pipeline.qdrant_store import QdrantStore
from models.document import IngestResponse

logger = logging.getLogger("ingestion-service")


class IngestionOrchestrator:
    def __init__(self):
        self.loader = PdfLoader()
        self.chunker = Chunker()
        self.embedder = BedrockEmbedder()
        self.store = QdrantStore()

    def ingest_file(self, source: str, file_bytes: bytes = None) -> IngestResponse:
        logger.info(f"Starting ingestion for: {source}")

        if file_bytes:
            pages = self.loader.load_bytes(file_bytes)
        else:
            pages = self.loader.load(source)

        chunks = self.chunker.chunk_pages(pages, source=source)

        texts = [c.text for c in chunks]
        embeddings = self.embedder.embed_batch(texts)
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding

        self.store.ensure_collection()
        self.store.upsert([
            {"id": c.id, "text": c.text, "embedding": c.embedding, "metadata": c.metadata}
            for c in chunks
        ])

        return IngestResponse(
            source=source,
            chunks_created=len(chunks),
            collection=self.store.collection,
        )