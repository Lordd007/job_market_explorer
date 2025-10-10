# utils/embedder.py
from __future__ import annotations
from sentence_transformers import SentenceTransformer
import threading

_model = None
_lock = threading.Lock()
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

def get_model():
    global _model
    with _lock:
        if _model is None:
            _model = SentenceTransformer(MODEL_NAME)
        return _model

def embed_text(text: str) -> list[float]:
    text = (text or "").strip()
    if not text:
        return [0.0] * 384  # MiniLM dimension; pgvector column is 768—we’ll pad or switch model to 768
    vec = get_model().encode(text, normalize_embeddings=True)
    return vec.tolist()
