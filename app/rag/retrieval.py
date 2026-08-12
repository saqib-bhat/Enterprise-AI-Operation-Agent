from __future__ import annotations
from typing import List, Dict, Any
from .embeddings import embed_texts, get_model
from .vector_store import load_index, index_exists
import numpy as np


def retrieve(query: str, top_k: int = 3) -> Dict[str, Any]:
    if not query or not query.strip():
        return {"success": False, "error": "Empty query"}

    idx_meta = load_index()
    if idx_meta[0] is None:
        return {"success": False, "error": "No index available"}
    index, metadata = idx_meta
    q_emb = embed_texts([query]).astype('float32')
    D, I = index.search(q_emb, top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        if idx < 0 or idx >= len(metadata):
            continue
        meta = metadata[idx]
        results.append({
            "chunk_id": meta.get('chunk_id'),
            "source": meta.get('source'),
            "page": meta.get('page'),
            "text": meta.get('text'),
            "score": float(score),
        })
    return {"success": True, "results": results}
