"""
Embedding & Indexing Pipeline
==============================
Reads chunks, generates embeddings via Google Gemini,
and stores them in Supabase (pgvector).

Handles free-tier rate limits:
  - 100 requests/minute (each text = 1 request)
  - 1,000 requests/day

Usage:
    python embed_and_store.py

Re-run safely — it resumes from where it left off.
"""

import json
import os
import logging
import time
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the backend/ directory (parent of scripts/)
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from google import genai
from google.genai import errors as genai_errors
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────
EMBEDDING_MODEL = "gemini-embedding-001"
BATCH_SIZE = 50        # Texts per API call (each text = 1 quota unit)
DELAY_BETWEEN = 35     # Seconds between batches (50 texts per 35s ≈ 85/min < 100 limit)
MAX_RETRIES = 3        # Retries per batch on rate limit
DAILY_BUDGET = 950     # Stop before hitting 1000/day to leave headroom

# Global genai client
_genai_client = None


def init_clients() -> tuple:
    """Initialize Google GenAI and Supabase clients."""
    global _genai_client

    google_api_key = os.environ.get("GOOGLE_API_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not all([google_api_key, supabase_url, supabase_key]):
        raise EnvironmentError(
            "Set GOOGLE_API_KEY, SUPABASE_URL, and SUPABASE_SERVICE_KEY env vars."
        )

    _genai_client = genai.Client(api_key=google_api_key)
    supabase: Client = create_client(supabase_url, supabase_key)
    return supabase


def load_chunks(path: str = "chunks.json") -> list[dict]:
    """Load chunks from JSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    logger.info(f"Loaded {len(data)} chunks")
    return data


def generate_embeddings_with_retry(texts: list[str]) -> list[list[float]] | None:
    """Generate embeddings with retry. Returns None if daily quota exhausted."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = _genai_client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
            )
            return [e.values for e in result.embeddings]

        except (genai_errors.ClientError, Exception) as e:
            error_str = str(e)
            if "429" not in error_str and "RESOURCE_EXHAUSTED" not in error_str:
                raise  # Not a rate limit error

            if "PerDay" in error_str:
                logger.warning("DAILY QUOTA EXHAUSTED. Stopping gracefully.")
                logger.warning("Re-run this script tomorrow — it will resume automatically.")
                return None

            # Per-minute limit — wait and retry
            wait = 65
            logger.warning(f"Per-minute rate limit (attempt {attempt}/{MAX_RETRIES}). Waiting {wait}s...")
            time.sleep(wait)

    logger.error("Max retries exceeded for this batch.")
    return None


def get_existing_chunk_ids(supabase: Client) -> set:
    """Fetch all chunk_ids already stored in Supabase."""
    existing_ids = set()
    offset = 0
    while True:
        resp = supabase.table("documents").select("chunk_id").range(offset, offset + 999).execute()
        if not resp.data:
            break
        existing_ids.update(row["chunk_id"] for row in resp.data)
        offset += 1000
    return existing_ids


def embed_and_store(chunks_path: str = "chunks.json"):
    """Main pipeline: embed chunks and store in Supabase."""
    supabase = init_clients()
    chunks = load_chunks(chunks_path)

    # Get existing chunks for resume support
    existing_ids = get_existing_chunk_ids(supabase)
    logger.info(f"Found {len(existing_ids)} chunks already in DB — will skip these")

    # Filter to only new chunks
    new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]
    total_new = len(new_chunks)

    if total_new == 0:
        logger.info("All chunks already stored! Nothing to do.")
        return

    logger.info(f"{total_new} new chunks to process (budget: {DAILY_BUDGET} texts/run)")

    texts_used = 0  # Track daily quota usage
    stored_this_run = 0

    for i in range(0, total_new, BATCH_SIZE):
        batch = new_chunks[i : i + BATCH_SIZE]
        texts = [c["content"] for c in batch]

        # Check daily budget
        if texts_used + len(texts) > DAILY_BUDGET:
            logger.info(f"Approaching daily budget ({texts_used}/{DAILY_BUDGET} used). Stopping.")
            logger.info("Re-run this script tomorrow to continue.")
            break

        batch_num = i // BATCH_SIZE + 1
        total_batches = (min(total_new, DAILY_BUDGET) + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info(f"Batch {batch_num}/{total_batches} — embedding {len(texts)} texts...")

        embeddings = generate_embeddings_with_retry(texts)

        if embeddings is None:
            # Daily quota hit or max retries — stop gracefully
            break

        # Prepare rows for upsert
        rows = []
        for chunk, embedding in zip(batch, embeddings):
            rows.append({
                "chunk_id": chunk["chunk_id"],
                "content": chunk["content"],
                "url": chunk["url"],
                "title": chunk["title"],
                "chunk_index": chunk["chunk_index"],
                "embedding": embedding,
            })

        # Upsert into Supabase
        supabase.table("documents").upsert(rows, on_conflict="chunk_id").execute()

        texts_used += len(texts)
        stored_this_run += len(rows)
        total_stored = len(existing_ids) + stored_this_run

        logger.info(f"Stored {len(rows)} rows | This run: {stored_this_run} | Total in DB: {total_stored} | Quota used: {texts_used}/{DAILY_BUDGET}")

        # Wait between batches to stay under per-minute limit
        if i + BATCH_SIZE < total_new:
            logger.info(f"Waiting {DELAY_BETWEEN}s before next batch...")
            time.sleep(DELAY_BETWEEN)

    logger.info(f"\n{'='*50}")
    logger.info(f"Run complete!")
    logger.info(f"Stored this run: {stored_this_run}")
    logger.info(f"Total in DB: {len(existing_ids) + stored_this_run}")
    logger.info(f"Remaining: {total_new - stored_this_run}")
    if total_new - stored_this_run > 0:
        logger.info(f"Run this script again tomorrow to process more.")
    else:
        logger.info(f"All chunks processed!")
    logger.info(f"{'='*50}")


if __name__ == "__main__":
    embed_and_store()
