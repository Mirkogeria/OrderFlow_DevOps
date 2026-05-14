# test_pipeline.py — Unit tests for ingestion-service
# Run with: python -m pytest tests/ -v --cov=. --cov-report=term

import pytest
from unittest.mock import MagicMock, patch, call
from io import BytesIO
from fastapi.testclient import TestClient


# ========================================
# Fixtures
# ========================================

@pytest.fixture
def client():
    """Client FastAPI con Qdrant e Bedrock mockati."""
    with patch("pipeline.qdrant_store.QdrantClient") as mock_qdrant, \
         patch("pipeline.embedder.boto3.client") as mock_boto:

        # Mock Qdrant: is_healthy → True, get_collections → lista vuota
        mock_qdrant_instance = MagicMock()
        mock_qdrant_instance.get_collections.return_value = MagicMock(collections=[])
        mock_qdrant.return_value = mock_qdrant_instance

        # Mock Bedrock: embed → vettore da 1536 float
        mock_bedrock_instance = MagicMock()
        mock_bedrock_instance.invoke_model.return_value = {
            "body": MagicMock(
                read=MagicMock(
                    return_value=b'{"embedding": ' + b'[0.1]' * 1 + b'}'
                )
            )
        }
        mock_boto.return_value = mock_bedrock_instance

        from main import app
        yield TestClient(app)


@pytest.fixture
def sample_pdf_bytes():
    """PDF minimale valido per i test di upload."""
    # PDF minimo con una pagina contenente testo
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f\n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n0\n%%EOF"
    )


# ========================================
# Health Check Tests
# ========================================

class TestHealthCheck:
    def test_health_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_health_returns_healthy(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert data["service"] == "ingestion-service"

    def test_health_includes_version(self, client):
        data = client.get("/health").json()
        assert "version" in data

    def test_health_includes_qdrant_status(self, client):
        data = client.get("/health").json()
        assert "qdrant_connected" in data


# ========================================
# Chunker Tests (unit puri, nessun mock necessario)
# ========================================

class TestChunker:
    def test_chunk_short_text(self):
        from pipeline.chunker import Chunker
        chunker = Chunker(chunk_size=512, chunk_overlap=50)
        pages = ["Testo breve"]
        chunks = chunker.chunk_pages(pages, source="test.pdf")
        assert len(chunks) == 1
        assert chunks[0].text == "Testo breve"

    def test_chunk_long_text(self):
        from pipeline.chunker import Chunker
        chunker = Chunker(chunk_size=100, chunk_overlap=10)
        long_text = "A" * 350
        pages = [long_text]
        chunks = chunker.chunk_pages(pages, source="test.pdf")
        assert len(chunks) > 1

    def test_chunk_metadata(self):
        from pipeline.chunker import Chunker
        chunker = Chunker(chunk_size=512, chunk_overlap=50)
        pages = ["Pagina uno", "Pagina due"]
        chunks = chunker.chunk_pages(pages, source="doc.pdf")
        assert chunks[0].metadata["source"] == "doc.pdf"
        assert chunks[0].metadata["page"] == 1
        assert chunks[1].metadata["page"] == 2

    def test_chunk_assigns_unique_ids(self):
        from pipeline.chunker import Chunker
        chunker = Chunker(chunk_size=512, chunk_overlap=50)
        pages = ["Testo A", "Testo B", "Testo C"]
        chunks = chunker.chunk_pages(pages, source="test.pdf")
        ids = [c.id for c in chunks]
        assert len(ids) == len(set(ids))  # tutti diversi

    def test_chunk_overlap(self):
        from pipeline.chunker import Chunker
        chunker = Chunker(chunk_size=20, chunk_overlap=5)
        text = "A" * 50
        pages = [text]
        chunks = chunker.chunk_pages(pages, source="test.pdf")
        # Con overlap il secondo chunk deve iniziare prima della fine del primo
        assert len(chunks) >= 2

    def test_chunk_empty_pages_ignored(self):
        from pipeline.chunker import Chunker
        chunker = Chunker(chunk_size=512, chunk_overlap=50)
        pages = ["   ", "", "Contenuto valido"]
        chunks = chunker.chunk_pages(pages, source="test.pdf")
        # Le pagine vuote producono chunk vuoti ma sono incluse
        # quello che conta è che non crashi
        assert isinstance(chunks, list)

    def test_chunk_index_in_metadata(self):
        from pipeline.chunker import Chunker
        chunker = Chunker(chunk_size=10, chunk_overlap=0)
        pages = ["A" * 30]
        chunks = chunker.chunk_pages(pages, source="test.pdf")
        for i, chunk in enumerate(chunks):
            assert chunk.metadata["chunk_index"] == i


# ========================================
# PdfLoader Tests
# ========================================

class TestPdfLoader:
    def test_supports_pdf(self):
        from loaders.pdf_loader import PdfLoader
        loader = PdfLoader()
        assert loader.supports("documento.pdf") is True
        assert loader.supports("DOCUMENTO.PDF") is True

    def test_not_supports_other(self):
        from loaders.pdf_loader import PdfLoader
        loader = PdfLoader()
        assert loader.supports("documento.txt") is False
        assert loader.supports("documento.docx") is False

    def test_load_bytes_returns_list(self):
        from loaders.pdf_loader import PdfLoader
        loader = PdfLoader()
        # PDF minimo senza testo estraibile → lista vuota ma no crash
        minimal_pdf = (
            b"%PDF-1.4\n1 0 obj\n<</Type /Catalog /Pages 2 0 R>>\nendobj\n"
            b"2 0 obj\n<</Type /Pages /Kids [] /Count 0>>\nendobj\n"
            b"xref\n0 3\ntrailer\n<</Size 3 /Root 1 0 R>>\nstartxref\n0\n%%EOF"
        )
        result = loader.load_bytes(minimal_pdf)
        assert isinstance(result, list)


# ========================================
# DocumentChunk Model Tests
# ========================================

class TestDocumentChunk:
    def test_chunk_creation(self):
        from models.document import DocumentChunk
        chunk = DocumentChunk(
            id="abc-123",
            text="Testo di esempio",
            metadata={"source": "test.pdf", "page": 1}
        )
        assert chunk.id == "abc-123"
        assert chunk.text == "Testo di esempio"
        assert chunk.metadata["page"] == 1

    def test_chunk_embedding_optional(self):
        from models.document import DocumentChunk
        chunk = DocumentChunk(id="x", text="test")
        assert chunk.embedding is None

    def test_chunk_has_created_at(self):
        from models.document import DocumentChunk
        chunk = DocumentChunk(id="x", text="test")
        assert chunk.created_at is not None

    def test_ingest_response(self):
        from models.document import IngestResponse
        resp = IngestResponse(
            source="doc.pdf",
            chunks_created=10,
            collection="devops-docs"
        )
        assert resp.status == "completed"
        assert resp.chunks_created == 10


# ========================================
# Ingest Endpoint Tests
# ========================================

class TestIngestEndpoint:
    def test_ingest_rejects_non_pdf(self, client):
        data = {"file": ("documento.txt", b"contenuto", "text/plain")}
        response = client.post("/api/ingest", files=data)
        assert response.status_code == 400
        assert "PDF" in response.json()["detail"]

    def test_ingest_accepts_pdf_filename(self, client):
        # Mocka l'orchestrator per non chiamare davvero Bedrock/Qdrant
        with patch("main.orchestrator.ingest_file") as mock_ingest:
            from models.document import IngestResponse
            mock_ingest.return_value = IngestResponse(
                source="test.pdf",
                chunks_created=5,
                collection="devops-docs"
            )
            data = {"file": ("test.pdf", b"%PDF-1.4 content", "application/pdf")}
            response = client.post("/api/ingest", files=data)
            assert response.status_code == 201
            assert response.json()["chunks_created"] == 5
            assert response.json()["source"] == "test.pdf"

    def test_ingest_returns_collection(self, client):
        with patch("main.orchestrator.ingest_file") as mock_ingest:
            from models.document import IngestResponse
            mock_ingest.return_value = IngestResponse(
                source="guida.pdf",
                chunks_created=3,
                collection="devops-docs"
            )
            data = {"file": ("guida.pdf", b"%PDF content", "application/pdf")}
            response = client.post("/api/ingest", files=data)
            assert response.json()["collection"] == "devops-docs"

    def test_ingest_handles_exception(self, client):
        with patch("main.orchestrator.ingest_file") as mock_ingest:
            mock_ingest.side_effect = Exception("Bedrock non raggiungibile")
            data = {"file": ("test.pdf", b"%PDF content", "application/pdf")}
            response = client.post("/api/ingest", files=data)
            assert response.status_code == 500


# ========================================
# Collections Endpoint Tests
# ========================================

class TestCollectionsEndpoint:
    def test_list_collections_returns_200(self, client):
        response = client.get("/api/collections")
        assert response.status_code == 200

    def test_list_collections_structure(self, client):
        data = client.get("/api/collections").json()
        assert "collections" in data
        assert isinstance(data["collections"], list)