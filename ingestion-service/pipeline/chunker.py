import uuid
import logging
from models.document import DocumentChunk
from config.settings import settings

logger = logging.getLogger("ingestion-service")


class Chunker:
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap

    def chunk_pages(self, pages: list[str], source: str) -> list[DocumentChunk]:
        chunks = []
        for page_num, page_text in enumerate(pages):
            page_chunks = self._chunk_text(page_text)
            for chunk_index, chunk_text in enumerate(page_chunks):
                chunk = DocumentChunk(
                    id=str(uuid.uuid4()),
                    text=chunk_text,
                    metadata={
                        "source": source,
                        "page": page_num + 1,
                        "chunk_index": chunk_index,
                    }
                )
                chunks.append(chunk)
        logger.info(f"Created {len(chunks)} chunks from {len(pages)} pages")
        return chunks

    def _chunk_text(self, text: str) -> list[str]:
        if len(text) <= self.chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start += self.chunk_size - self.chunk_overlap
        return chunks