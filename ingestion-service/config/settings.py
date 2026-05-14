from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    aws_region: str = "eu-central-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    bedrock_embedding_model: str = "amazon.titan-embed-text-v1"

    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "devops-docs"

    chunk_size: int = 512
    chunk_overlap: int = 50

    environment: str = "development"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()