from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # AWS / Bedrock
    aws_region: str = "eu-central-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    bedrock_embedding_model: str = "amazon.titan-embed-text-v1"

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "devops-docs"

    # RAG
    retriever_top_k: int = 4
    max_tokens: int = 1024
    temperature: float = 0.1

    # Memoria conversazione
    memory_max_messages: int = 10

    # App
    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()