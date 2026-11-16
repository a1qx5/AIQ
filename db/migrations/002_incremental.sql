-- Migration 002: Add incremental ingestion tracking
-- This migration adds support for detecting unchanged documents and tracking pipeline changes

-- Step 1: Add text_hash column to chunks table for detecting changed chunks
ALTER TABLE chunks ADD COLUMN text_hash text;

-- Step 2: Backfill text_hash for existing chunks
UPDATE chunks SET text_hash = encode(sha256(convert_to(text, 'UTF8')), 'hex');

-- Step 3: Make text_hash NOT NULL now that it's backfilled
ALTER TABLE chunks ALTER COLUMN text_hash SET NOT NULL;

-- Step 4: Create ingestions tracking table
-- This table tracks when each document was last ingested for each embedding model
-- and stores the content hash and pipeline fingerprint to detect changes
CREATE TABLE ingestions (
    document_id          bigint NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    embedding_model      text   NOT NULL,
    content_hash         text   NOT NULL,
    pipeline_fingerprint text   NOT NULL,
    ingested_at          timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (document_id, embedding_model)
);

-- Step 5: Backfill ingestions table from existing chunks
-- For each (document, embedding_model) pair that has chunks, create an ingestions row
-- Use the content_hash from documents table and 'legacy' as placeholder fingerprint
INSERT INTO ingestions (document_id, embedding_model, content_hash, pipeline_fingerprint, ingested_at)
SELECT DISTINCT
    c.document_id,
    c.embedding_model,
    COALESCE(d.content_hash, ''),
    'legacy',
    MIN(d.ingested_at)
FROM chunks c
JOIN documents d ON c.document_id = d.id
GROUP BY c.document_id, c.embedding_model, d.content_hash, d.ingested_at;
