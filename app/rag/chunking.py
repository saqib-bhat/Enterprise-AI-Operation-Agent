from __future__ import annotations
from typing import List, Dict
from pathlib import Path
import uuid


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 200) -> List[str]:
    if not text:
        return []
    tokens = text.split()
    chunks = []
    i = 0
    while i < len(tokens):
        chunk_tokens = tokens[i : i + chunk_size]
        chunks.append(" ".join(chunk_tokens))
        i += max(1, chunk_size - overlap)
    return chunks


def chunk_documents(docs: List[Dict], chunk_size: int = 800, overlap: int = 200) -> List[Dict]:
    result = []
    for d in docs:
        text = d.get('text', '')
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
        for idx, c in enumerate(chunks):
            result.append({
                "chunk_id": str(uuid.uuid4()),
                "source": d.get('source'),
                "page": d.get('page'),
                "text": c,
                "chunk_index": idx,
            })
    return result
