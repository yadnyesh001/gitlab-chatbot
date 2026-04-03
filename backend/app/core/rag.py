"""
RAG Pipeline
=============
Retrieves relevant context from the vector store and generates
grounded answers using Gemini LLM via the google-genai SDK.
"""

import logging
from dataclasses import dataclass

from google import genai
from google.genai import types

from app.core.config import get_settings
from app.core.vector_store import search_documents

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a helpful assistant that answers questions about GitLab — specifically \
about the GitLab Handbook and GitLab Direction pages.

RULES:
1. Answer ONLY based on the provided context below. Do NOT use prior knowledge.
2. If the context does not contain enough information to answer, say: \
   "I don't have enough information from the GitLab Handbook to answer this question."
3. Be concise and accurate. Use bullet points for lists.
4. When referencing information, mention which source it came from.
5. Do NOT make up information, URLs, or page references.
6. If the question is not related to GitLab, politely decline and explain \
   that you can only answer questions about the GitLab Handbook and Direction pages.

CONTEXT:
{context}
"""

_genai_client = None


def _get_client():
    """Get or create Google GenAI client (singleton)."""
    global _genai_client
    if _genai_client is None:
        settings = get_settings()
        _genai_client = genai.Client(api_key=settings.google_api_key)
    return _genai_client


@dataclass
class Source:
    title: str
    url: str
    similarity: float


@dataclass
class ChatResponse:
    answer: str
    sources: list[Source]
    context_used: bool  # Whether relevant context was found


def build_context(documents: list[dict]) -> str:
    """Format retrieved documents into a context string."""
    if not documents:
        return "No relevant documents found."

    parts = []
    for i, doc in enumerate(documents, 1):
        parts.append(
            f"[Source {i}: {doc['title']}]\n"
            f"URL: {doc['url']}\n"
            f"{doc['content']}\n"
        )
    return "\n---\n".join(parts)


def generate_answer(question: str) -> ChatResponse:
    """
    Full RAG pipeline:
    1. Retrieve relevant chunks
    2. Build context
    3. Generate grounded answer
    """
    settings = get_settings()
    client = _get_client()

    # Step 1: Retrieve
    documents = search_documents(question)
    context_used = len(documents) > 0

    # Step 2: Build context
    context = build_context(documents)

    # Step 3: Generate with Gemini
    system_instruction = SYSTEM_PROMPT.replace("{context}", context)

    response = client.models.generate_content(
        model=settings.llm_model,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.3,
            max_output_tokens=1024,
        ),
    )

    answer = response.text

    # Build sources
    sources = [
        Source(
            title=doc["title"],
            url=doc["url"],
            similarity=round(doc["similarity"], 3),
        )
        for doc in documents
    ]

    # Deduplicate sources by URL
    seen_urls = set()
    unique_sources = []
    for s in sources:
        if s.url not in seen_urls:
            seen_urls.add(s.url)
            unique_sources.append(s)

    logger.info(f"Generated answer with {len(unique_sources)} sources")

    return ChatResponse(
        answer=answer,
        sources=unique_sources,
        context_used=context_used,
    )
