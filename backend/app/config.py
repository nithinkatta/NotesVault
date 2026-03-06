from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment."""

    # Database (MongoDB)
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "notes"
    mongo_collection: str = "notes"

    # File uploads (local vs S3)
    use_local_uploads: bool = True  # toggle off to use S3 for uploads
    uploads_dir: str = "data/uploads"
    aws_region: str = "us-east-1"
    s3_bucket: str = "ai-notes-media"

    # API + AI
    api_base_url: str = "http://localhost:8000"
    # Provide via environment: GEMINI_API_KEY
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3-flash-preview"
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
