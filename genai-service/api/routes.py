from fastapi import APIRouter, HTTPException
import logging
from models.chat_models import ChatRequest, ChatResponse
from chains.rag_chain import RAGChain
from memory.conversation_memory import ConversationMemory
from config.settings import settings

logger = logging.getLogger("genai-service")
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """Endpoint principale: riceve una domanda e restituisce la risposta RAG."""
    try:
        chain = RAGChain(session_id=request.session_id)
        result = chain.run(question=request.question)
        return ChatResponse(
            answer=result["answer"],
            session_id=request.session_id,
            sources=result["sources"],
            model=result["model"],
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
def clear_session(session_id: str):
    """Cancella la memoria di una sessione."""
    memory = ConversationMemory(session_id=session_id)
    memory.clear()
    return {"message": f"Session {session_id} cleared"}


@router.get("/sessions/{session_id}/history")
def get_history(session_id: str):
    """Restituisce lo storico di una sessione."""
    memory = ConversationMemory(session_id=session_id)
    return {
        "session_id": session_id,
        "messages": memory.get_history(),
        "total": len(memory.get_history()),
    }