from pypdf import PdfReader
from io import BytesIO
import logging
from loaders.base_loader import BaseLoader

logger = logging.getLogger("ingestion-service")


class PdfLoader(BaseLoader):
    def supports(self, source: str) -> bool:
        return source.lower().endswith(".pdf")

    def load(self, source: str) -> list[str]:
        logger.info(f"Loading PDF: {source}")
        reader = PdfReader(source)
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())
        logger.info(f"Loaded {len(pages)} pages from {source}")
        return pages

    def load_bytes(self, data: bytes) -> list[str]:
        reader = PdfReader(BytesIO(data))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text and text.strip():
                pages.append(text.strip())
        return pages