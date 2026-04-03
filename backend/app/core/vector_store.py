"""
Vector Store — Supabase pgvector Integration
=============================================
Handles embedding queries and retrieving similar documents.
"""

import logging

from google import genai
from supabase import create_client, Client

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None
_genai_client = None


def get_supabase() -> Client:
    """Get or create Supabase client (singleton)."""
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _supabase_client


def get_genai_client():
    """Get or create Google GenAI client (singleton)."""
    global _genai_client
    if _genai_client is None:
        settings = get_settings()
        _genai_client = genai.Client(api_key=settings.google_api_key)
    return _genai_client


def embed_query(text: str) -> list[float]:
    """Generate embedding for a user query."""
    settings = get_settings()
    client = get_genai_client()

    result = client.models.embed_content(
        model=settings.embedding_model,
        contents=text,
    )
    return result.embeddings[0].values


def search_documents(query: str, top_k: int | None = None) -> list[dict]:
    """
    Embed the query and search Supabase for similar documents.
    Returns list of {content, url, title, similarity}.
    """
    settings = get_settings()
    k = top_k or settings.top_k

    # Generate query embedding
    query_embedding = embed_query(query)

    # Call the Supabase RPC function
    supabase = get_supabase()
    response = supabase.rpc(
        "match_documents",
        {
            "query_embedding": query_embedding,
            "match_count": k,
            "match_threshold": settings.similarity_threshold,
        },
    ).execute()

    results = response.data or []
    logger.info(f"Found {len(results)} matching documents for query: {query[:50]}...")
    return results
