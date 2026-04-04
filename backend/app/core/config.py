"""
Application Configuration
==========================
Loads settings from environment variables with validation.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Google Gemini (for LLM)
    google_api_key: str

    # Cohere (for embeddings)
    cohere_api_key: str

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # RAG settings
    embedding_model: str = "embed-english-v3.0"
    llm_model: str = "gemini-2.5-flash"
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
