# utils/embedder.py
from __future__ import annotations
from fastembed import TextEmbedding
import threading
import math

# Small, good-quality 384-dim model
_MODEL_NAME = "BAAI/bge-small-en-v1.5"

_model = None
_lock = threading.Lock()

def get_model() -> TextEmbedding:
    global _model
    with _lock:
        if _model is None:
            _model = TextEmbedding(model_name=_MODEL_NAME)
        return _model

def _l2(v: list[float]) -> float:
    return math.sqrt(sum(x*x for x in v)) or 1.0

def embed_text(text: str) -> list[float]:
    """Return a 384-dim normalized vector suitable for cosine (<#>) search."""
    text = (text or "").strip()
    if not text:
        return [0.0] * 384
    model = get_model()
    vec = list(next(model.embed([text])))
    # normalize to unit length (defensive; many fastembed models already are)
    n = _l2(vec)
    return [x / n for x in vec]
