from __future__ import annotations

from typing import Dict, Any

import numpy as np

from .embeddings import embed_texts
from .vector_store import load_index


# FAISS IndexFlatL2 returns squared Euclidean distance.
# Lower distance means greater similarity.
#
# Results above this threshold are considered too weak
# to be reliable evidence.
MAX_L2_DISTANCE = 1.0


def retrieve(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Retrieve relevant document chunks for a query."""

    if not query or not query.strip():
        return {
            "success": False,
            "error": "Empty query",
        }

    # Load persisted FAISS index and metadata.
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

    # Generate query embedding.
    try:
        q_emb = embed_texts([query]).astype("float32")
    except Exception:
        return {
            "success": False,
            "error": "RAG embedding model unavailable",
        }

    # Search FAISS.
    D, I = index.search(q_emb, top_k)

    results = []

    for score, idx in zip(D[0], I[0]):

        if idx < 0 or idx >= len(metadata):
            continue

        distance = float(score)

        # Reject weak semantic matches.
        if distance > MAX_L2_DISTANCE:
            continue

        meta = metadata[idx]

        results.append(
            {
                "chunk_id": meta.get("chunk_id"),
                "source": meta.get("source"),
                "page": meta.get("page"),
                "text": meta.get("text"),
                "score": distance,
            }
        )

    return {
        "success": True,
        "results": results,
    }