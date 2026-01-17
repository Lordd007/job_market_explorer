# ingest/seed_sample.py
import json
import datetime as dt

from sqlalchemy.orm import Session

from db.session import SessionLocal
from db.models import Job
from core.hashing import text_hash


def _ensure_bytes(x) -> bytes:
    """
    Postgres BYTEA needs bytes/bytearray/memoryview.
    Our text_hash() currently returns str, so convert safely.

    - If it's hex (common for hashes), bytes.fromhex() works.
    - Otherwise, fall back to UTF-8 encoding.
    """
    if x is None:
        return b""
    if isinstance(x, (bytes, bytearray, memoryview)):
        return bytes(x)
    if isinstance(x, str):
        s = x.strip()
        try:
            return bytes.fromhex(s)
        except ValueError:
            return s.encode("utf-8")
    # last resort
    return str(x).encode("utf-8")


def run():
    db: Session = SessionLocal()
    try:
        with open("data/seed_jobs.json", "r", encoding="utf-8") as f:
            items = json.load(f)

        added = 0
        for it in items:
            url = it.get("url")
            if not url:
                continue

            
            exists = db.query(Job).filter_by(url=url).first()
            if exists:
                continue

            
            h = text_hash(it.get("title"), it.get("company"), it.get("description_text"))
            desc_hash_bytes = _ensure_bytes(h)

            posted_at = None
            if it.get("posted_at"):
                posted_at = dt.datetime.fromisoformat(it["posted_at"])

            job = Job(
                title=it.get("title"),
                company=it.get("company"),
                city=it.get("city"),
                region=it.get("region"),
                country=it.get("country"),
                posted_at=posted_at,
                source=it.get("source", "seed"),
                url=url,
                description_text=it.get("description_text"),
                desc_hash=desc_hash_bytes,
            )

            db.add(job)
            added += 1

        db.commit()
        print(f"Seeded {added} jobs")
    finally:
        db.close()


if __name__ == "__main__":
    run()
