from __future__ import annotations
from typing import List
import threading
import numpy as np

_MODEL = None
_LOCK = threading.Lock()
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def get_model(model_name: str = _MODEL_NAME):
    global _MODEL
    if _MODEL is None:
        with _LOCK:
            if _MODEL is None:
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as exc:
                    raise RuntimeError(
                        "sentence-transformers is required for RAG embeddings but is not installed or cannot be imported. "
                        "Please install sentence-transformers in the current .venv."
                    ) from exc

                try:
                    _MODEL = SentenceTransformer(model_name, device="cpu")
                except Exception as exc:
                    raise RuntimeError(
                        f"Failed to load embedding model '{model_name}' on CPU. "
                        "Check the sentence-transformers and torch installation."
                    ) from exc
    return _MODEL


def embed_texts(texts: List[str]):
    model = get_model()
    try:
        return model.encode(
            texts,
            show_progress_bar=False,
            convert_to_numpy=True,
            device="cpu"
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to encode texts with embedding model '{_MODEL_NAME}': {exc}"
        ) from exc
