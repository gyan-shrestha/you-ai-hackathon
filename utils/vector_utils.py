import numpy as np
from sentence_transformers import SentenceTransformer

# Local embedding model
_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
_dim = _model.get_sentence_embedding_dimension()


def embed_texts(texts):
    """Convert texts to normalized embeddings."""
    return _model.encode(texts, normalize_embeddings=True).astype("float32")

