#!/usr/bin/env python3
"""
Show EXPLAIN ANALYZE for a sample search query.
"""

import os
import numpy as np
import psycopg
from pgvector.psycopg import register_vector
from dotenv import load_dotenv
from aiq.embedders import model_id

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

# Create a random query vector
query_embedding = np.random.rand(1024)

# Run EXPLAIN ANALYZE
print("EXPLAIN ANALYZE for vector search query:")
print("=" * 80)

result = conn.execute(
    """
    EXPLAIN (ANALYZE, BUFFERS)
    SELECT d.source_path, c.heading_path, 1 - (c.embedding <=> %s) AS score
    FROM chunks c
    JOIN documents d ON d.id = c.document_id
    WHERE c.client = %s AND c.embedding_model = %s
    ORDER BY c.embedding <=> %s
    LIMIT 20
    """,
    (query_embedding, "lumina", model_id("bge-m3"), query_embedding)
).fetchall()

for row in result:
    print(row[0])

conn.close()
