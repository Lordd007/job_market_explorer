# scripts/backfill_desc_hash_bin.py
import os, math
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from db.session import SessionLocal
from ingest.dedupe import normalize_text, sha256_bytes


BATCH = 1000
with SessionLocal() as db:
    while True:
        rows = db.execute(text("""
            SELECT job_id, description_text
            FROM jobs
            WHERE desc_hash_bin IS NULL
            LIMIT :n
        """), {"n": BATCH}).fetchall()
        if not rows: break

        for job_id, desc in rows:
            h = sha256_bytes(normalize_text(desc or ""))
            db.execute(text("""
                UPDATE jobs SET desc_hash_bin=:h WHERE job_id=:id
            """), {"h": h, "id": job_id})
        db.commit()
        print(f"Backfilled {len(rows)} rows...")
print("Done.")
