import logging
import boto3
import json
from chains.prompt_templates import RAG_PROMPT, FALLBACK_PROMPT
from retriever.qdrant_retriever import QdrantRetriever
from memory.conversation_memory import ConversationMemory
from config.settings import settings

logger = logging.getLogger("genai-service")


class RAGChain:
    """Catena RAG: recupera contesto → costruisce prompt → chiama Claude su Bedrock."""

    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.retriever = QdrantRetriever()
        self.memory = ConversationMemory(
            session_id=session_id,
            max_messages=settings.memory_max_messages,
        )
        self.bedrock = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
        )

    def _call_claude(self, prompt: str) -> str:
        """Chiama Claude 3 su Bedrock e restituisce la risposta."""
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": settings.max_tokens,
            "temperature": settings.temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        })
        response = self.bedrock.invoke_model(
            modelId=settings.bedrock_model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        result = json.loads(response["body"].read())
        return result["content"][0]["text"]

    def run(self, question: str) -> dict:
        """Esegue la chain RAG completa e restituisce risposta + fonti."""
        # 1. Recupera chunk rilevanti
        chunks = self.retriever.retrieve(question)
        sources = list({c["source"] for c in chunks})

        # 2. Costruisce il contesto
        context = "\n\n".join([
            f"[{c['source']} - pagina {c['page']}]\n{c['text']}"
            for c in chunks
        ])

        # 3. Recupera storico conversazione
        chat_history = self.memory.format_history()

        # 4. Costruisce il prompt
        if context.strip():
            prompt = RAG_PROMPT.format(
                context=context,
                chat_history=chat_history,
                question=question,
            )
        else:
            logger.warning("No relevant context found, using fallback prompt")
            prompt = FALLBACK_PROMPT.format(
                chat_history=chat_history,
                question=question,
            )

        # 5. Chiama Claude
        answer = self._call_claude(prompt)

        # 6. Aggiorna memoria
        self.memory.add_message("user", question)
        self.memory.add_message("assistant", answer)

        logger.info(f"RAG chain completed for session={self.session_id}")
        return {
            "answer": answer,
            "sources": sources,
            "model": settings.bedrock_model_id,
        }