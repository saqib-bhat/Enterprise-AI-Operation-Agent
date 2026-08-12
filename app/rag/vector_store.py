from __future__ import annotations
from typing import List, Dict, Any
from pathlib import Path
import faiss
import numpy as np
import json


INDEX_PATH = Path("vector_store/index.faiss")
METADATA_PATH = Path("vector_store/metadata.json")


def ensure_dirs():
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)


def build_index(embeddings: List[List[float]]) -> faiss.Index:
    # accept numpy arrays or lists
    if isinstance(embeddings, np.ndarray):
        arr = embeddings.astype('float32')
    else:
        arr = np.array(embeddings).astype('float32') if embeddings is not None else np.empty((0,))

    if arr.size == 0:
        # empty index with dim 1
        index = faiss.IndexFlatL2(1)
        return index

    if arr.ndim == 1:
        arr = arr.reshape(1, -1)

    dim = arr.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(arr)
    return index


def save_index(index: faiss.Index, metadata: List[Dict[str, Any]]):
    ensure_dirs()
    faiss.write_index(index, str(INDEX_PATH))
    with METADATA_PATH.open('w', encoding='utf-8') as fo:
        json.dump(metadata, fo, ensure_ascii=False)


def load_index():
    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        return None, []
    index = faiss.read_index(str(INDEX_PATH))
    import json
    with METADATA_PATH.open('r', encoding='utf-8') as fo:
        metadata = json.load(fo)
    return index, metadata


def index_exists() -> bool:
    return INDEX_PATH.exists() and METADATA_PATH.exists()
