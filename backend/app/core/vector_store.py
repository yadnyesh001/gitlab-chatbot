"""
Vector Store — Supabase pgvector Integration
=============================================
Handles embedding queries (via Cohere) and retrieving similar documents.
"""

import logging
import cohere

from supabase import create_client, Client
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_supabase_client: Client | None = None
_cohere_client = None

EMBEDDING_MODEL = "embed-english-v3.0"  # 1024 dimensions


def get_supabase() -> Client:
    """Get or create Supabase client (singleton)."""
    global _supabase_client
    if _supabase_client is None:
        settings = get_settings()
        _supabase_client = create_client(settings.supabase_url, settings.supabase_service_key)
    return _supabase_client


def get_cohere_client():
    """Get or create Cohere client (singleton)."""
    global _cohere_client
    if _cohere_client is None:
        settings = get_settings()
        _cohere_client = cohere.Client(api_key=settings.cohere_api_key)
    return _cohere_client


def embed_query(text: str) -> list[float]:
    """Generate embedding for a user query using Cohere."""
    client = get_cohere_client()
    response = client.embed(
        texts=[text],
        model=EMBEDDING_MODEL,
        input_type="search_query",
    )
    return response.embeddings[0]


def embed_documents(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for documents using Cohere."""
    client = get_cohere_client()
    response = client.embed(
        texts=texts,
        model=EMBEDDING_MODEL,
        input_type="search_document",
    )
    return response.embeddings


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
