from __future__ import annotations

from typing import Dict, Any

import numpy as np

from .embeddings import embed_texts
from .vector_store import load_index


def retrieve(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Retrieve the most relevant document chunks for a query."""

    if not query or not query.strip():
        return {
            "success": False,
            "error": "Empty query",
        }

    # Load the persisted FAISS index and its metadata.
    index, metadata = load_index()

    if index is None:
        return {
            "success": False,
            "error": "No index available",
        }

    if not metadata:
        return {
            "success": True,
            "results": [],
        }

    # Generate the embedding for the user query.
    try:
        q_emb = embed_texts([query]).astype("float32")
    except Exception:
        # Embedding model initialization or encoding failed.
        # Return a controlled failure without exposing internal details.
        return {
            "success": False,
            "error": "RAG embedding model unavailable",
        }

    # Search the FAISS index.
    D, I = index.search(q_emb, top_k)

    results = []

    for score, idx in zip(D[0], I[0]):
        if idx < 0 or idx >= len(metadata):
            continue

        meta = metadata[idx]

        results.append(
            {
                "chunk_id": meta.get("chunk_id"),
                "source": meta.get("source"),
                "page": meta.get("page"),
                "text": meta.get("text"),
                "score": float(score),
            }
        )

    return {
        "success": True,
        "results": results,
    }
