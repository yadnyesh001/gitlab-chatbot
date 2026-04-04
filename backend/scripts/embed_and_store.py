"""
Embedding & Indexing Pipeline
==============================
Reads chunks, generates embeddings via Cohere,
and stores them in Supabase (pgvector).

Cohere free tier: 10,000 API calls/month, no daily limit issues.

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

import cohere
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────
EMBEDDING_MODEL = "embed-english-v3.0"  # 1024 dimensions
BATCH_SIZE = 50        # Smaller batches to stay under 100K tokens/min
DELAY_BETWEEN = 8      # Seconds between batches (~6 batches/min × ~15K tokens = ~90K/min)


def init_clients() -> tuple:
    """Initialize Cohere and Supabase clients."""
    cohere_api_key = os.environ.get("COHERE_API_KEY")
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY")

    if not all([cohere_api_key, supabase_url, supabase_key]):
        raise EnvironmentError(
            "Set COHERE_API_KEY, SUPABASE_URL, and SUPABASE_SERVICE_KEY env vars."
        )

    co = cohere.Client(api_key=cohere_api_key)
    supabase: Client = create_client(supabase_url, supabase_key)
    return co, supabase


def load_chunks(path: str = "chunks.json") -> list[dict]:
    """Load chunks from JSON."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    logger.info(f"Loaded {len(data)} chunks")
    return data


def generate_embeddings(co: cohere.Client, texts: list[str]) -> list[list[float]]:
    """Generate embeddings using Cohere."""
    response = co.embed(
        texts=texts,
        model=EMBEDDING_MODEL,
        input_type="search_document",
    )
    return response.embeddings


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
    co, supabase = init_clients()
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

    logger.info(f"{total_new} new chunks to process")

    stored_count = 0

    for i in range(0, total_new, BATCH_SIZE):
        batch = new_chunks[i : i + BATCH_SIZE]
        texts = [c["content"] for c in batch]

        batch_num = i // BATCH_SIZE + 1
        total_batches = (total_new + BATCH_SIZE - 1) // BATCH_SIZE
        logger.info(f"Batch {batch_num}/{total_batches} — embedding {len(texts)} texts...")

        try:
            embeddings = generate_embeddings(co, texts)
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            logger.info(f"Stored {stored_count} chunks before error. Re-run to continue.")
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

        stored_count += len(rows)
        total_stored = len(existing_ids) + stored_count

        logger.info(f"Stored {len(rows)} rows | This run: {stored_count} | Total in DB: {total_stored}")

        # Small delay between batches
        if i + BATCH_SIZE < total_new:
            time.sleep(DELAY_BETWEEN)

    logger.info(f"\n{'='*50}")
    logger.info(f"Run complete!")
    logger.info(f"Stored this run: {stored_count}")
    logger.info(f"Total in DB: {len(existing_ids) + stored_count}")
    remaining = total_new - stored_count
    if remaining > 0:
        logger.info(f"Remaining: {remaining} — re-run to continue.")
    else:
        logger.info(f"All chunks processed!")
    logger.info(f"{'='*50}")


if __name__ == "__main__":
    embed_and_store()
