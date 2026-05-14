import boto3
import json
import logging
from config.settings import settings

logger = logging.getLogger("ingestion-service")


class BedrockEmbedder:
    def __init__(self):
        self.client = boto3.client(
            "bedrock-runtime",
            region_name=settings.aws_region,
        )
        self.model_id = settings.bedrock_embedding_model

    def embed(self, text: str) -> list[float]:
        body = json.dumps({"inputText": text})
        response = self.client.invoke_model(
            modelId=self.model_id,
            contentType="application/json",
            accept="application/json",
            body=body,
        )
        result = json.loads(response["body"].read())
        return result["embedding"]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for i, text in enumerate(texts):
            logger.debug(f"Embedding chunk {i+1}/{len(texts)}")
            embeddings.append(self.embed(text))
        return embeddings