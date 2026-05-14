# test_rag.py — Unit tests for genai-service
# Run with: python -m pytest tests/ -v --cov=. --cov-report=term

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


# ========================================
# Fixtures
# ========================================

@pytest.fixture(autouse=True)
def clear_memory():
    """Svuota la memoria tra ogni test."""
    from memory.conversation_memory import ConversationMemory
    ConversationMemory.clear_all()
    yield
    ConversationMemory.clear_all()


@pytest.fixture
def client():
    """Client FastAPI con Qdrant e Bedrock mockati."""
    with patch("retriever.qdrant_retriever.QdrantClient") as mock_qdrant, \
         patch("retriever.qdrant_retriever.boto3.client") as mock_boto_retriever, \
         patch("chains.rag_chain.boto3.client") as mock_boto_chain, \
         patch("main.boto3.client"):

        # Mock Qdrant
        mock_qdrant_instance = MagicMock()
        mock_qdrant_instance.get_collections.return_value = MagicMock(collections=[])
        mock_qdrant_instance.search.return_value = []
        mock_qdrant.return_value = mock_qdrant_instance

        # Mock Bedrock per embedding
        mock_embed = MagicMock()
        mock_embed.invoke_model.return_value = {
            "body": MagicMock(read=MagicMock(
                return_value=b'{"embedding": [0.1, 0.2, 0.3]}'
            ))
        }
        mock_boto_retriever.return_value = mock_embed

        # Mock Bedrock per Claude
        mock_claude = MagicMock()
        mock_claude.invoke_model.return_value = {
            "body": MagicMock(read=MagicMock(
                return_value=b'{"content": [{"text": "Risposta di test"}]}'
            ))
        }
        mock_boto_chain.return_value = mock_claude

        from main import app
        yield TestClient(app)


@pytest.fixture
def chat_request():
    return {
        "question": "Cosa è Kubernetes?",
        "session_id": "test-session-001",
        "stream": False
    }


# ========================================
# Health Check Tests
# ========================================

class TestHealthCheck:
    def test_health_returns_200(self, client):
        assert client.get("/health").status_code == 200

    def test_health_returns_healthy(self, client):
        data = client.get("/health").json()
        assert data["status"] == "healthy"
        assert data["service"] == "genai-service"

    def test_health_includes_version(self, client):
        assert "version" in client.get("/health").json()

    def test_health_includes_bedrock_status(self, client):
        assert "bedrock_available" in client.get("/health").json()

    def test_health_includes_qdrant_status(self, client):
        assert "qdrant_connected" in client.get("/health").json()


# ========================================
# ConversationMemory Tests (unit puri)
# ========================================

class TestConversationMemory:
    def test_empty_history_initially(self):
        from memory.conversation_memory import ConversationMemory
        mem = ConversationMemory(session_id="new-session")
        assert mem.get_history() == []

    def test_add_message(self):
        from memory.conversation_memory import ConversationMemory
        mem = ConversationMemory(session_id="s1")
        mem.add_message("user", "Ciao")
        history = mem.get_history()
        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Ciao"

    def test_add_multiple_messages(self):
        from memory.conversation_memory import ConversationMemory
        mem = ConversationMemory(session_id="s2")
        mem.add_message("user", "Domanda 1")
        mem.add_message("assistant", "Risposta 1")
        mem.add_message("user", "Domanda 2")
        assert len(mem.get_history()) == 3

    def test_max_messages_limit(self):
        from memory.conversation_memory import ConversationMemory
        mem = ConversationMemory(session_id="s3", max_messages=4)
        for i in range(10):
            mem.add_message("user", f"Messaggio {i}")
        assert len(mem.get_history()) == 4

    def test_format_history_empty(self):
        from memory.conversation_memory import ConversationMemory
        mem = ConversationMemory(session_id="s4")
        formatted = mem.format_history()
        assert "Nessuna" in formatted

    def test_format_history_with_messages(self):
        from memory.conversation_memory import ConversationMemory
        mem = ConversationMemory(session_id="s5")
        mem.add_message("user", "Ciao")
        mem.add_message("assistant", "Ciao! Come posso aiutarti?")
        formatted = mem.format_history()
        assert "Utente" in formatted
        assert "Assistente" in formatted
        assert "Ciao" in formatted

    def test_clear_session(self):
        from memory.conversation_memory import ConversationMemory
        mem = ConversationMemory(session_id="s6")
        mem.add_message("user", "Test")
        mem.clear()
        assert mem.get_history() == []

    def test_sessions_are_isolated(self):
        from memory.conversation_memory import ConversationMemory
        mem_a = ConversationMemory(session_id="session-A")
        mem_b = ConversationMemory(session_id="session-B")
        mem_a.add_message("user", "Solo per A")
        assert len(mem_b.get_history()) == 0
        assert len(mem_a.get_history()) == 1

    def test_clear_all(self):
        from memory.conversation_memory import ConversationMemory
        ConversationMemory(session_id="x").add_message("user", "test")
        ConversationMemory(session_id="y").add_message("user", "test")
        ConversationMemory.clear_all()
        assert ConversationMemory(session_id="x").get_history() == []
        assert ConversationMemory(session_id="y").get_history() == []


# ========================================
# Prompt Templates Tests
# ========================================

class TestPromptTemplates:
    def test_rag_prompt_renders(self):
        from chains.prompt_templates import RAG_PROMPT
        result = RAG_PROMPT.format(
            context="Contesto di test",
            chat_history="Nessuna conversazione precedente.",
            question="Cosa è Docker?"
        )
        assert "Cosa è Docker?" in result
        assert "Contesto di test" in result

    def test_fallback_prompt_renders(self):
        from chains.prompt_templates import FALLBACK_PROMPT
        result = FALLBACK_PROMPT.format(
            chat_history="Nessuna conversazione precedente.",
            question="Cosa è Terraform?"
        )
        assert "Cosa è Terraform?" in result

    def test_rag_prompt_includes_history(self):
        from chains.prompt_templates import RAG_PROMPT
        result = RAG_PROMPT.format(
            context="ctx",
            chat_history="Utente: domanda precedente\nAssistente: risposta",
            question="Nuova domanda"
        )
        assert "domanda precedente" in result


# ========================================
# Chat Endpoint Tests
# ========================================

class TestChatEndpoint:
    def test_chat_returns_200(self, client, chat_request):
        response = client.post("/api/chat", json=chat_request)
        assert response.status_code == 200

    def test_chat_returns_answer(self, client, chat_request):
        data = client.post("/api/chat", json=chat_request).json()
        assert "answer" in data
        assert len(data["answer"]) > 0

    def test_chat_returns_session_id(self, client, chat_request):
        data = client.post("/api/chat", json=chat_request).json()
        assert data["session_id"] == "test-session-001"

    def test_chat_returns_model(self, client, chat_request):
        data = client.post("/api/chat", json=chat_request).json()
        assert "model" in data
        assert "claude" in data["model"]

    def test_chat_returns_sources(self, client, chat_request):
        data = client.post("/api/chat", json=chat_request).json()
        assert "sources" in data
        assert isinstance(data["sources"], list)

    def test_chat_missing_question(self, client):
        response = client.post("/api/chat", json={"session_id": "s1"})
        assert response.status_code == 422

    def test_chat_default_session_id(self, client):
        response = client.post("/api/chat", json={"question": "Test"})
        assert response.status_code == 200
        assert response.json()["session_id"] == "default"


# ========================================
# Session Management Tests
# ========================================

class TestSessionManagement:
    def test_get_empty_history(self, client):
        response = client.get("/api/sessions/nuova-sessione/history")
        assert response.status_code == 200
        data = response.json()
        assert data["messages"] == []
        assert data["total"] == 0

    def test_history_after_chat(self, client):
        client.post("/api/chat", json={
            "question": "Cosa è Docker?",
            "session_id": "sessione-test"
        })
        data = client.get("/api/sessions/sessione-test/history").json()
        assert data["total"] == 2  # user + assistant
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"

    def test_clear_session(self, client):
        # Prima crea un po' di storia
        client.post("/api/chat", json={
            "question": "Test",
            "session_id": "da-cancellare"
        })
        # Poi cancella
        response = client.delete("/api/sessions/da-cancellare")
        assert response.status_code == 200
        # Verifica che sia vuota
        data = client.get("/api/sessions/da-cancellare/history").json()
        assert data["total"] == 0

    def test_sessions_are_isolated(self, client):
        client.post("/api/chat", json={"question": "Domanda A", "session_id": "sessione-A"})
        data_b = client.get("/api/sessions/sessione-B/history").json()
        assert data_b["total"] == 0