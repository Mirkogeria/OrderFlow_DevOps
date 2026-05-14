import boto3
import json
import logging
from fastapi.responses import StreamingResponse
from retriever.qdrant_retriever import QdrantRetriever
from memory.conversation_memory import ConversationMemory
from chains.prompt_templates import RAG_PROMPT, FALLBACK_PROMPT
from config.settings import settings

logger = logging.getLogger("genai-service")


def stream_chat(question: str, session_id: str = "default") -> StreamingResponse:
    """Genera una risposta in streaming da Claude su Bedrock."""
    retriever = QdrantRetriever()
    memory = ConversationMemory(session_id=session_id)
    bedrock = boto3.client("bedrock-runtime", region_name=settings.aws_region)

    chunks = retriever.retrieve(question)
    context = "\n\n".join([
        f"[{c['source']} - pagina {c['page']}]\n{c['text']}"
        for c in chunks
    ])
    chat_history = memory.format_history()

    if context.strip():
        prompt = RAG_PROMPT.format(
            context=context,
            chat_history=chat_history,
            question=question,
        )
    else:
        prompt = FALLBACK_PROMPT.format(
            chat_history=chat_history,
            question=question,
        )

    def generate():
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": settings.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        })
        response = bedrock.invoke_model_with_response_stream(
            modelId=settings.bedrock_model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        full_answer = []
        for event in response["body"]:
            chunk_data = json.loads(event["chunk"]["bytes"])
            if chunk_data.get("type") == "content_block_delta":
                text = chunk_data["delta"].get("text", "")
                full_answer.append(text)
                yield text

        # Salva in memoria dopo lo streaming
        memory.add_message("user", question)
        memory.add_message("assistant", "".join(full_answer))

    return StreamingResponse(generate(), media_type="text/plain")