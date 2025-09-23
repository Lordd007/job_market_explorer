import hashlib
def text_hash(*parts: str) -> str:
    norm = " ".join((p or "").strip().lower() for p in parts)
    return hashlib.sha1(norm.encode("utf-8")).hexdigest()
