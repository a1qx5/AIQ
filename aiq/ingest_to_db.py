#!/usr/bin/env python3
"""
Ingest markdown documents from a source directory into PostgreSQL with pgvector.
Supports incremental ingestion with change detection and orphan removal.

Usage (from the project root):
  python -m aiq.ingest_to_db <model> [--source-dir PATH] [--source NAME]
                                     [--dry-run] [--force]
  where <model> is "bge-m3" or "voyage"
  --source-dir: directory containing markdown files (default: data/dummy_v2_md)
  --source: source identifier for documents (default: sharepoint)
  --dry-run: show what would happen without making changes
  --force: bypass safety guards (e.g., 30% deletion threshold)
"""

import sys
import os
import hashlib
import argparse
import time
from pathlib import Path
from datetime import datetime, timezone
import psycopg
from pgvector.psycopg import register_vector
from dotenv import load_dotenv

from aiq.chunking import (chunk_markdown, build_embed_text, EMBED_TEMPLATE,
                          MAX_CHARS, OVERLAP, MIN_SECTION_CHARS, MERGE_LIMIT)
from aiq.config import MD_DIR
from aiq.embedders import get_embedder


def compute_lock_key(source, model):
    """
    Compute a stable 64-bit integer key for pg_advisory_lock.

    The lock prevents concurrent ingestion runs for the same (source, model) pair.
    We use the first 8 bytes of SHA256(source + model) as a signed 64-bit integer.

    Note: PostgreSQL advisory locks use bigint (signed 64-bit), so we need to
    convert the hash bytes to a signed integer in the range [-2^63, 2^63-1].
    """
    combined = f"{source}:{model}"
    hash_bytes = hashlib.sha256(combined.encode('utf-8')).digest()
    # Take first 8 bytes and interpret as signed 64-bit integer
    return int.from_bytes(hash_bytes[:8], byteorder='big', signed=True)


def compute_pipeline_fingerprint():
    """
    Compute a fingerprint of the chunking and embedding pipeline.

    This includes:
    - Chunking constants (MAX_CHARS, OVERLAP, MIN_SECTION_CHARS, MERGE_LIMIT)
    - Embed-text template structure

    If any of these change, all documents should be re-processed.
    """
    # Import chunking module to read current values
    from aiq import chunking as ch

    # Same template object that prepare_embed_text uses (defined once, in chunking.py)
    template = ch.EMBED_TEMPLATE

    # Combine all pipeline parameters
    components = [
        f"MAX_CHARS={ch.MAX_CHARS}",
        f"OVERLAP={ch.OVERLAP}",
        f"MIN_SECTION_CHARS={ch.MIN_SECTION_CHARS}",
        f"MERGE_LIMIT={ch.MERGE_LIMIT}",
        f"TEMPLATE={template}",
    ]

    pipeline_string = "|".join(components)
    return hashlib.sha256(pipeline_string.encode('utf-8')).hexdigest()


def extract_client_from_filename(md_path):
    """Extract client name from filename: last '-' separated part, lowercased."""
    return md_path.stem.split("-")[-1].lower()


def extract_document_date(md_path):
    """Extract document date from YYYY-MM prefix of filename."""
    stem = md_path.stem
    parts = stem.split("-")
    if len(parts) >= 2:
        try:
            year = int(parts[0])
            month = int(parts[1])
            return f"{year}-{month:02d}-01"
        except ValueError:
            pass
    return None


def compute_text_hash(text):
    """SHA256 hex digest of a text. Used for chunk text and for whole documents."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


# Same function under a second name, kept on purpose: tests/test_ingestion.py (test D)
# patches `compute_text_hash` to break one chunk and must not affect the document hash.
compute_content_hash = compute_text_hash


def prepare_embed_text(client, file_stem, chunk):
    """Prepare the text to be embedded for a chunk."""
    return build_embed_text(client, file_stem, chunk['heading_path'], chunk['text'])


def check_if_unchanged(conn, document_id, model_name, content_hash, pipeline_fingerprint):
    """
    Check if a document needs re-processing.

    Returns True if the document is unchanged (same content_hash and pipeline_fingerprint).
    """
    result = conn.execute(
        """
        SELECT 1 FROM ingestions
        WHERE document_id = %s
          AND embedding_model = %s
          AND content_hash = %s
          AND pipeline_fingerprint = %s
        """,
        (document_id, model_name, content_hash, pipeline_fingerprint)
    )
    return result.fetchone() is not None


def ingest_document(conn, md_path, model_name, embedder, source, pipeline_fingerprint, dry_run=False):
    """
    Ingest a single document into the database.

    Returns: (status, client, chunk_count)
    where status is 'NEW', 'UPDATED', or 'UNCHANGED'
    """
    # Read markdown content
    markdown_text = md_path.read_text(encoding='utf-8')

    # Extract metadata
    client = extract_client_from_filename(md_path)
    source_path = md_path.name
    document_date = extract_document_date(md_path)
    source_modified_at = datetime.fromtimestamp(
        md_path.stat().st_mtime,
        tz=timezone.utc
    )
    content_hash = compute_content_hash(markdown_text)

    # Check if document already exists
    result = conn.execute(
        """
        SELECT id FROM documents
        WHERE client = %s AND source = %s AND source_path = %s
        """,
        (client, source, source_path)
    )
    existing_doc = result.fetchone()

    if existing_doc:
        document_id = existing_doc[0]
        # Check if document is unchanged
        if check_if_unchanged(conn, document_id, model_name, content_hash, pipeline_fingerprint):
            return ('UNCHANGED', client, 0)
        status = 'UPDATED'
    else:
        status = 'NEW'
        document_id = None

    if dry_run:
        # In dry-run mode, we need to know the chunk count for reporting
        chunks = chunk_markdown(markdown_text, source_path)
        return (status, client, len(chunks))

    # Chunk the document
    chunks = chunk_markdown(markdown_text, source_path)

    # Prepare texts for embedding
    file_stem = md_path.stem
    texts_to_embed = []
    for chunk in chunks:
        embed_text = prepare_embed_text(client, file_stem, chunk)
        texts_to_embed.append(embed_text)

    # Generate embeddings
    embeddings = embedder(texts_to_embed, is_query=False)

    # Start transaction
    try:
        with conn.transaction():
            # UPSERT document
            result = conn.execute(
                """
                INSERT INTO documents
                    (client, source, source_path, document_date, source_modified_at, content_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (client, source, source_path)
                DO UPDATE SET
                    document_date = EXCLUDED.document_date,
                    source_modified_at = EXCLUDED.source_modified_at,
                    content_hash = EXCLUDED.content_hash,
                    ingested_at = now()
                RETURNING id
                """,
                (client, source, source_path, document_date, source_modified_at, content_hash)
            )
            document_id = result.fetchone()[0]

            # DELETE existing chunks for this document and model
            conn.execute(
                "DELETE FROM chunks WHERE document_id = %s AND embedding_model = %s",
                (document_id, model_name)
            )

            # INSERT new chunks with text_hash
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                text_hash = compute_text_hash(chunk['text'])
                conn.execute(
                    """
                    INSERT INTO chunks
                        (document_id, client, chunk_index, heading_path, text, embedding, embedding_model, text_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        document_id,
                        client,
                        chunk['chunk_index'],
                        chunk['heading_path'],
                        chunk['text'],
                        embedding.tolist(),
                        model_name,
                        text_hash
                    )
                )

            # UPSERT ingestions tracking row
            conn.execute(
                """
                INSERT INTO ingestions
                    (document_id, embedding_model, content_hash, pipeline_fingerprint, ingested_at)
                VALUES (%s, %s, %s, %s, now())
                ON CONFLICT (document_id, embedding_model)
                DO UPDATE SET
                    content_hash = EXCLUDED.content_hash,
                    pipeline_fingerprint = EXCLUDED.pipeline_fingerprint,
                    ingested_at = now()
                """,
                (document_id, model_name, content_hash, pipeline_fingerprint)
            )

        return (status, client, len(chunks))

    except Exception as e:
        # Transaction will be rolled back automatically
        raise e


def remove_orphaned_documents(conn, source, existing_files, force=False, dry_run=False):
    """
    Remove documents from the database that no longer exist in the source directory.

    A document belongs to a source, not to a model, so removal is for ALL models:
    the delete cascades to its chunks and ingestions rows for every embedding model.

    Safety guard: refuse to delete more than 30% of documents unless --force is given.

    Returns: list of removed document paths
    """
    # Get all documents for this source
    result = conn.execute(
        """
        SELECT id, source_path FROM documents
        WHERE source = %s
        ORDER BY source_path
        """,
        (source,)
    )
    db_documents = {row[1]: row[0] for row in result.fetchall()}

    # Find orphaned documents
    existing_filenames = {f.name for f in existing_files}
    orphaned = {path: doc_id for path, doc_id in db_documents.items()
                if path not in existing_filenames}

    if not orphaned:
        return []

    # Safety guard: check deletion percentage
    total_docs = len(db_documents)
    orphan_count = len(orphaned)
    deletion_percentage = (orphan_count / total_docs * 100) if total_docs > 0 else 0

    if deletion_percentage > 30 and not force:
        print(f"\nERROR: Refusing to delete {orphan_count} documents ({deletion_percentage:.1f}% of {total_docs} total).")
        print(f"This exceeds the 30% safety threshold.")
        print(f"Use --force to override this safety guard.")
        sys.exit(1)

    # Additional safety: refuse if source directory is empty
    if len(existing_filenames) == 0 and not force:
        print(f"\nERROR: Source directory is empty but {total_docs} documents exist in database.")
        print(f"Refusing to delete all documents. Use --force to override.")
        sys.exit(1)

    if dry_run:
        return list(orphaned.keys())

    # Delete orphaned documents (cascades to chunks and ingestions)
    for path, doc_id in orphaned.items():
        conn.execute(
            "DELETE FROM documents WHERE id = %s",
            (doc_id,)
        )

    conn.commit()
    return list(orphaned.keys())


def main():
    parser = argparse.ArgumentParser(
        description='Ingest markdown documents into PostgreSQL with incremental processing'
    )
    parser.add_argument('model', choices=['bge-m3', 'voyage'],
                        help='Embedding model to use')
    parser.add_argument('--source-dir', type=str, default=str(MD_DIR),
                        help=f'Directory containing markdown files (default: {MD_DIR})')
    parser.add_argument('--source', type=str, default='sharepoint',
                        help='Source identifier for documents (default: sharepoint)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would happen without making changes')
    parser.add_argument('--force', action='store_true',
                        help='Bypass safety guards (e.g., 30%% deletion threshold)')
    parser.add_argument('--inject-sleep', type=float, default=0,
                        help=argparse.SUPPRESS)  # Hidden flag for testing concurrency

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Compute pipeline fingerprint
    pipeline_fingerprint = compute_pipeline_fingerprint()

    # Connect to database
    db_password = os.getenv("POSTGRES_PASSWORD")
    if not db_password:
        print("Error: POSTGRES_PASSWORD not found in .env")
        sys.exit(1)

    conn = psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname="ai",
        user="ai",
        password=db_password,
        autocommit=True  # Use autocommit for individual transactions
    )

    # Register vector type
    register_vector(conn)

    # Acquire advisory lock for this (source, model) pair
    lock_key = compute_lock_key(args.source, args.model)
    result = conn.execute(
        "SELECT pg_try_advisory_lock(%s)",
        (lock_key,)
    ).fetchone()

    if not result[0]:
        print(f"another ingestion for {args.source}/{args.model} is running")
        conn.close()
        sys.exit(1)

    # Hidden flag for concurrency testing: sleep after acquiring lock
    if args.inject_sleep > 0:
        time.sleep(args.inject_sleep)

    # Wrap all processing in try-finally to ensure lock release
    try:
        # Load the embedding model only after the lock is held: loading is slow, and a run
        # that cannot get the lock should exit at once instead of loading the model first.
        embedder = None if args.dry_run else get_embedder(args.model)

        # Process all markdown files
        md_dir = Path(args.source_dir)
        if not md_dir.exists():
            print(f"Error: Source directory '{args.source_dir}' does not exist")
            sys.exit(1)

        md_files = sorted(md_dir.glob("*.md"))

        # Track statistics
        stats = {
            'NEW': 0,
            'UPDATED': 0,
            'UNCHANGED': 0,
            'REMOVED': 0,
            'FAILED': 0
        }
        total_chunks_embedded = 0

        # Process each file
        for md_path in md_files:
            try:
                status, client, chunk_count = ingest_document(
                    conn, md_path, args.model, embedder, args.source,
                    pipeline_fingerprint, dry_run=args.dry_run
                )
                stats[status] += 1

                # Only count chunks that were actually embedded
                if status != 'UNCHANGED' and not args.dry_run:
                    total_chunks_embedded += chunk_count

                # Fix cosmetic issue: "1 chunks" -> "1 chunk"
                chunk_word = "chunk" if chunk_count == 1 else "chunks"

                if args.dry_run:
                    print(f"{status}: {md_path.name} ({client}, {chunk_count} {chunk_word})")
                else:
                    if status == 'UNCHANGED':
                        print(f"{status}: {md_path.name} ({client})")
                    else:
                        print(f"{status}: {md_path.name} ({client}, {chunk_count} {chunk_word})")

            except Exception as e:
                stats['FAILED'] += 1
                print(f"FAILED: {md_path.name} - {str(e)}")
                # Continue processing remaining files

        # Remove orphaned documents
        removed_paths = remove_orphaned_documents(
            conn, args.source, md_files,
            force=args.force, dry_run=args.dry_run
        )
        stats['REMOVED'] = len(removed_paths)

        if removed_paths:
            for path in removed_paths:
                print(f"REMOVED: {path}")

        # Print summary
        print(f"\nSummary: {stats['NEW']} new, {stats['UPDATED']} updated, "
              f"{stats['UNCHANGED']} unchanged, {stats['REMOVED']} removed, "
              f"{stats['FAILED']} failed")
        print(f"Chunks embedded: {total_chunks_embedded}")

        # Non-zero exit code when any file failed, so callers and scripts can tell.
        if stats['FAILED']:
            sys.exit(1)

    finally:
        # Always release advisory lock and close connection
        try:
            conn.execute("SELECT pg_advisory_unlock(%s)", (lock_key,))
        except Exception:
            pass  # Lock will be released when connection closes anyway
        finally:
            conn.close()


if __name__ == "__main__":
    main()
