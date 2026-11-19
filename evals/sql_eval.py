#!/usr/bin/env python3
"""
Evaluate retrieval performance using SQL queries against PostgreSQL + pgvector.

Usage: python -m evals.sql_eval <model>
  where <model> is "bge-m3" or "voyage"
"""

import sys
import os
import json
from pathlib import Path
import psycopg
from pgvector.psycopg import register_vector
from dotenv import load_dotenv

from aiq.embedders import get_embedder, model_id
from aiq.questions import load_questions


def get_client_chunks_count(conn, model_name):
    """Get count of chunks per client for this model."""
    result = conn.execute(
        "SELECT client, COUNT(*) FROM chunks WHERE embedding_model = %s GROUP BY client",
        (model_name,)
    ).fetchall()
    return {row[0]: row[1] for row in result}


def search_chunks(conn, query_embedding, client, model_name, limit=20):
    """
    Search for nearest chunks using vector similarity.

    Returns list of (source_path, heading_path, score) tuples.
    """
    results = conn.execute(
        """
        SELECT d.source_path, c.heading_path, 1 - (c.embedding <=> %s) AS score
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.client = %s AND c.embedding_model = %s
        ORDER BY c.embedding <=> %s
        LIMIT %s
        """,
        (query_embedding, client, model_name, query_embedding, limit)
    ).fetchall()
    return results


def evaluate(conn, embedder, model_name, questions):
    """
    Evaluate retrieval performance.

    Returns list of result dictionaries with:
    - id: question ID
    - kind: "answerable" or "unanswerable"
    - rank: position of correct document (1-based) or None
    - best_score: highest similarity score
    - trap: trap type (if any)
    """
    # Get chunk counts per client
    client_counts = get_client_chunks_count(conn, model_name)

    results = []
    for q in questions:
        client = q["client"].lower()

        # Skip questions for clients with no chunks
        if client not in client_counts or client_counts[client] == 0:
            continue

        # Embed the question
        query_embedding = embedder([q["question"]], is_query=True)[0]

        # Search for nearest chunks
        search_results = search_chunks(conn, query_embedding, client, model_name, limit=20)

        # Get best score
        best_score = search_results[0][2] if search_results else 0.0

        # Handle unanswerable questions
        if q["expected_answer"] == "NOT_IN_CORPUS" or not q.get("source_file"):
            results.append({
                "id": q["id"],
                "kind": "unanswerable",
                "rank": None,
                "best_score": best_score,
                "trap": q.get("trap_type")
            })
            continue

        # For answerable questions, find rank of correct document
        source_stem = Path(q["source_file"]).stem
        rank = None
        for position, (source_path, heading_path, score) in enumerate(search_results, start=1):
            result_stem = Path(source_path).stem
            if result_stem == source_stem:
                rank = position
                break

        results.append({
            "id": q["id"],
            "kind": "answerable",
            "rank": rank,
            "best_score": best_score,
            "trap": q.get("trap_type")
        })

    return results


def main():
    if len(sys.argv) != 2:
        print("Usage: python -m evals.sql_eval <model>")
        print("  where <model> is 'bge-m3' or 'voyage'")
        sys.exit(1)

    model_name = sys.argv[1]
    if model_name not in ["bge-m3", "voyage"]:
        print(f"Error: Unknown model '{model_name}'. Use 'bge-m3' or 'voyage'.")
        sys.exit(1)

    # Load environment variables
    load_dotenv()

    # Get embedder
    embedder = get_embedder(model_name)

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
        password=db_password
    )

    # Register vector type
    register_vector(conn)

    # Load questions
    questions = load_questions()

    # Run evaluation
    # The database stores the full model id, not the short command-line name.
    results = evaluate(conn, embedder, model_id(model_name), questions)

    # Calculate metrics
    answerable = [r for r in results if r["kind"] == "answerable"]

    print(f"\n=== {model_name} (stored as {model_id(model_name)}) ===")
    print(f"Total questions: {len(questions)}")
    print(f"Evaluated: {len(results)} (skipped questions for clients with no chunks)")
    print(f"Answerable: {len(answerable)}")

    for k in (1, 3, 5):
        hits = sum(1 for r in answerable if r["rank"] is not None and r["rank"] <= k)
        print(f"hit@{k}: {hits}/{len(answerable)}")

    if answerable:
        mean_best = sum(r["best_score"] for r in answerable) / len(answerable)
        print(f"mean best score (answerable): {mean_best:.2f}")

    # Print unanswerable questions
    unanswerable = [r for r in results if r["kind"] == "unanswerable"]
    if unanswerable:
        print(f"\nUnanswerable questions ({len(unanswerable)}):")
        for r in unanswerable:
            print(f"  {r['id']}: best score {r['best_score']:.2f}")

    conn.close()


if __name__ == "__main__":
    main()
