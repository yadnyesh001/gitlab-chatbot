-- ============================================================
-- Supabase pgvector Schema for GitLab Handbook Chatbot
-- ============================================================
-- Run this in Supabase SQL Editor (Dashboard → SQL Editor → New Query)

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the documents table
CREATE TABLE IF NOT EXISTS documents (
    id            BIGSERIAL PRIMARY KEY,
    chunk_id      TEXT UNIQUE NOT NULL,
    content       TEXT NOT NULL,
    url           TEXT NOT NULL,
    title         TEXT NOT NULL,
    chunk_index   INTEGER NOT NULL,
    embedding     VECTOR(1024),           -- Cohere embed-english-v3.0 = 1024 dims
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Create HNSW index for fast similarity search (1024 dims is under 2000 limit)
CREATE INDEX IF NOT EXISTS documents_embedding_idx
ON documents
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- 4. Create index on chunk_id for upserts
CREATE INDEX IF NOT EXISTS documents_chunk_id_idx ON documents (chunk_id);

-- 5. Create the similarity search function
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1024),
    match_count     INT DEFAULT 5,
    match_threshold FLOAT DEFAULT 0.5
)
RETURNS TABLE (
    id          BIGINT,
    chunk_id    TEXT,
    content     TEXT,
    url         TEXT,
    title       TEXT,
    similarity  FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.chunk_id,
        d.content,
        d.url,
        d.title,
        1 - (d.embedding <=> query_embedding) AS similarity
    FROM documents d
    WHERE 1 - (d.embedding <=> query_embedding) > match_threshold
    ORDER BY d.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
