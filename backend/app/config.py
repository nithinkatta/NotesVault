from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment."""

    # Storage / data backends
    use_local_store: bool = True  # toggle off to use DynamoDB/S3
    data_dir: str = "data"
    uploads_dir: str = "data/uploads"

    # AWS (used when use_local_store=False)
    aws_region: str = "us-east-1"
    dynamo_table: str = "notes"
    s3_bucket: str = "ai-notes-media"

    # API + AI
    api_base_url: str = "http://localhost:8000"
    # Provide via environment: OPENAI_API_KEY
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    allowed_origins: List[str] = ["http://localhost:5173"]
    environment: str = "local"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
