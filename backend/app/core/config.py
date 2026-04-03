"""
Application Configuration
==========================
Loads settings from environment variables with validation.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Google Gemini
    google_api_key: str

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # RAG settings
    embedding_model: str = "gemini-embedding-001"
    llm_model: str = "gemini-2.0-flash"
    top_k: int = 5
    similarity_threshold: float = 0.5

    # App
    app_name: str = "GitLab Handbook Chatbot"
    cors_origins: str = "*"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
