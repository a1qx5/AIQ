#!/usr/bin/env python3
"""
Isolation tests for PostgreSQL schema constraints.
"""

import os
import sys
import json
import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from dotenv import load_dotenv

from embedders import get_embedder


def test_fk_violation():
    """
    Test that inserting a chunk with a client that differs from its document's
    client fails with a foreign key error.
    """
    print("Test 1: FK violation for mismatched client")
    print("=" * 60)

    load_dotenv()
    db_password = os.getenv("POSTGRES_PASSWORD")

    conn = psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname="ai",
        user="ai",
        password=db_password
    )
    register_vector(conn)

    try:
        with conn.transaction():
            # Get a document ID for a specific client
            result = conn.execute(
                "SELECT id, client FROM documents WHERE client = 'lumina' LIMIT 1"
            ).fetchone()

            if not result:
                print("ERROR: No lumina documents found")
                return

            doc_id, doc_client = result
            print(f"Using document ID {doc_id} (client: {doc_client})")

            # Try to insert a chunk with a DIFFERENT client
            wrong_client = "technova"  # Different from lumina
            fake_embedding = np.random.rand(1024).tolist()

            print(f"Attempting to insert chunk with client='{wrong_client}' for document with client='{doc_client}'")

            conn.execute(
                """
                INSERT INTO chunks
                    (document_id, client, chunk_index, heading_path, text, embedding, embedding_model)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (doc_id, wrong_client, 9999, "Test", "Test chunk", fake_embedding, "test-model")
            )

            # If we get here, the insert succeeded (which is bad)
            print("FAIL: Insert succeeded when it should have failed!")
            raise Exception("FK violation test failed")

    except psycopg.errors.ForeignKeyViolation as e:
        print(f"SUCCESS: Got expected FK violation error")
        print(f"Error message: {e}")
        # Rollback is automatic when exiting the with block
    except Exception as e:
        print(f"FAIL: Got unexpected error: {e}")
        raise
    finally:
        conn.close()

    print()


def test_cross_client_search():
    """
    Test that searching for a different client returns only that client's results.
    """
    print("Test 2: Cross-client search isolation")
    print("=" * 60)

    load_dotenv()
    db_password = os.getenv("POSTGRES_PASSWORD")

    conn = psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname="ai",
        user="ai",
        password=db_password
    )
    register_vector(conn)

    # Load one question per client
    with open("eval_questions.json", encoding="utf-8") as f:
        questions = json.load(f)

    # Find one question for each client
    client_questions = {}
    for q in questions:
        client = q["client"].lower()
        if client not in client_questions and client != "all":
            client_questions[client] = q

    embedder = get_embedder("bge-m3")

    for search_client in ["lumina", "ecobuild", "technova"]:
        print(f"\nSearching with client filter: {search_client}")

        # Get a question from ANY client (use the first one we have)
        question = list(client_questions.values())[0]
        print(f"Using question: {question['id']} (original client: {question['client'].lower()})")

        # Embed the question
        query_embedding = embedder([question["question"]], is_query=True)[0]

        # Search with the DIFFERENT client filter
        results = conn.execute(
            """
            SELECT d.source_path, c.client, 1 - (c.embedding <=> %s) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.client = %s AND c.embedding_model = %s
            ORDER BY c.embedding <=> %s
            LIMIT 5
            """,
            (query_embedding, search_client, "bge-m3", query_embedding)
        ).fetchall()

        print(f"Results (top 5):")
        for source_path, client, score in results:
            print(f"  {source_path}: client={client}, score={score:.3f}")

            # Verify all results have the expected client
            if client != search_client:
                print(f"FAIL: Found result with client '{client}' when filtering for '{search_client}'")
                conn.close()
                sys.exit(1)

        print(f"SUCCESS: All {len(results)} results have client='{search_client}'")

    conn.close()
    print()


if __name__ == "__main__":
    test_fk_violation()
    test_cross_client_search()
    print("\nAll isolation tests passed!")
