"""
API Routes
===========
FastAPI endpoints for the chatbot.
"""

import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.rag import generate_answer
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Suggested questions for new users ─────────────────────
SUGGESTED_QUESTIONS = [
    "What is GitLab's mission?",
    "How does GitLab approach remote work?",
    "What is GitLab's product direction for AI?",
    "How does GitLab handle incident management?",
    "What are GitLab's company values?",
]


# ── Request/Response Models ──────────────────────────────
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)


class SourceResponse(BaseModel):
    title: str
    url: str
    similarity: float


class ChatResponseModel(BaseModel):
    answer: str
    sources: list[SourceResponse]
    context_used: bool


class HealthResponse(BaseModel):
    status: str
    app_name: str
    timestamp: str


# ── Endpoints ────────────────────────────────────────────
@router.post("/chat", response_model=ChatResponseModel)
async def chat(request: ChatRequest):
    """Process a user question and return a grounded answer."""
    try:
        logger.info(f"Received question: {request.question[:80]}...")
        result = generate_answer(request.question)

        return ChatResponseModel(
            answer=result.answer,
            sources=[
                SourceResponse(title=s.title, url=s.url, similarity=s.similarity)
                for s in result.sources
            ],
            context_used=result.context_used,
        )
    except Exception as e:
        logger.error(f"Error processing question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process your question. Please try again.")


@router.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/suggested-questions")
async def suggested_questions():
    """Return suggested questions for new users."""
    return {"questions": SUGGESTED_QUESTIONS}
