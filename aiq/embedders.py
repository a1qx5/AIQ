import numpy as np

VOYAGE_MODEL = "voyage-multilingual-2"   # check the model names on your Voyage dashboard
VOYAGE_BATCH_SIZE = 32


def normalize(vectors):
    """Scale every vector to length 1, so a dot product equals cosine similarity."""
    vectors = np.array(vectors, dtype="float32")
    return vectors / np.linalg.norm(vectors, axis=1, keepdims=True)


BGE_M3_MODEL = "BAAI/bge-m3"


def model_id(name):
    """The id stored in chunks.embedding_model and ingestions.embedding_model.
    The command line keeps the short names; the database gets the full id, so that
    changing the underlying model (e.g. VOYAGE_MODEL) counts as a new model and
    vectors from different models are never mixed."""
    if name == "bge-m3":
        return BGE_M3_MODEL
    if name == "voyage":
        return f"voyage:{VOYAGE_MODEL}"
    raise ValueError(f"Unknown embedder: {name}")


def get_embedder(name):
    """Returns a function embed(texts, is_query) -> normalized numpy matrix."""
    if name == "bge-m3":
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(BGE_M3_MODEL)

        def embed(texts, is_query):
            # bge-m3 treats queries and documents the same way
            return normalize(model.encode(texts, batch_size=8))

        return embed

    if name == "voyage":
        import os
        import voyageai
        client = voyageai.Client(api_key=os.environ["VOYAGE_API_KEY"])

        def embed(texts, is_query):
            input_type = "query" if is_query else "document"
            all_vectors = []
            for start in range(0, len(texts), VOYAGE_BATCH_SIZE):
                batch = texts[start:start + VOYAGE_BATCH_SIZE]
                result = client.embed(batch, model=VOYAGE_MODEL, input_type=input_type)
                all_vectors.extend(result.embeddings)
            return normalize(all_vectors)

        return embed

    raise ValueError(f"Unknown embedder: {name}")