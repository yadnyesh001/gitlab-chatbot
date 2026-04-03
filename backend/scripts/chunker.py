"""
Text Chunking Pipeline
=======================
Loads scraped pages and splits them into overlapping chunks
suitable for embedding and vector search.
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict

from langchain.text_splitter import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

CHUNK_SIZE = 1000       # Characters per chunk
CHUNK_OVERLAP = 200     # Overlap between consecutive chunks


@dataclass
class Chunk:
    chunk_id: str
    content: str
    url: str
    title: str
    chunk_index: int


def load_scraped_pages(path: str = "scraped_pages.json") -> list[dict]:
    """Load scraped pages from JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    logger.info(f"Loaded {len(data)} pages from {path}")
    return data


def chunk_pages(pages: list[dict]) -> list[Chunk]:
    """Split pages into overlapping chunks with metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    chunks: list[Chunk] = []

    for page in pages:
        texts = splitter.split_text(page["content"])
        for i, text in enumerate(texts):
            chunk = Chunk(
                chunk_id=f"{page['content_hash']}_{i}",
                content=text,
                url=page["url"],
                title=page["title"],
                chunk_index=i,
            )
            chunks.append(chunk)

    logger.info(f"Created {len(chunks)} chunks from {len(pages)} pages")
    return chunks


def save_chunks(chunks: list[Chunk], output_path: str = "chunks.json"):
    """Save chunks to JSON."""
    data = [asdict(c) for c in chunks]
    Path(output_path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info(f"Saved {len(chunks)} chunks to {output_path}")


if __name__ == "__main__":
    pages = load_scraped_pages("scraped_pages.json")
    chunks = chunk_pages(pages)
    save_chunks(chunks, "chunks.json")
    print(f"\nDone! {len(chunks)} chunks ready for embedding.")
    if chunks:
        print(f"\nSample chunk:\n{chunks[0].content[:300]}...")
