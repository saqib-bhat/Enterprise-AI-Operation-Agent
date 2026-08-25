from __future__ import annotations

import ctypes
import os
import platform
from importlib.util import find_spec

from typing import List
import threading
import numpy as np

_MODEL = None
_LOCK = threading.Lock()
_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _preload_windows_torch_dlls() -> None:
    """Preload PyTorch's c10.dll on Windows before importing torch."""
    if platform.system() != "Windows":
        return

    try:
        spec = find_spec("torch")
        if not spec or not spec.origin:
            return

        torch_dir = os.path.dirname(spec.origin)
        c10_path = os.path.join(torch_dir, "lib", "c10.dll")

        if os.path.exists(c10_path):
            ctypes.CDLL(os.path.normpath(c10_path))
    except Exception:
        # Best-effort workaround. Normal torch import will handle failure.
        pass

def get_model(model_name: str = _MODEL_NAME):
    global _MODEL
    if _MODEL is None:
        with _LOCK:
            if _MODEL is None:
                _preload_windows_torch_dlls()
                try:
                    from sentence_transformers import SentenceTransformer
                except ImportError as exc:
                    raise RuntimeError(
                        "RAG embedding model unavailable: sentence-transformers is not installed or cannot be imported."
                    ) from exc

                try:
                    _MODEL = SentenceTransformer(model_name, device="cpu")
                except Exception as exc:
                    raise RuntimeError(
                        "RAG embedding model unavailable: failed to initialize the embedding model. "
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
