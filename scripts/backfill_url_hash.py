# scripts/backfill_url_hash.py
from __future__ import annotations
import argparse
from sqlalchemy import text
from db.session import SessionLocal
from ingest.dedupe import canonicalize_url, sha256_bytes

BATCH = 1000

def backfill_url_hash(merge_duplicates: bool = False):
    with SessionLocal() as db:
        last_id = None  # seek cursor over primary key

        while True:
            if last_id is None:
                rows = db.execute(text("""
                    SELECT job_id, url
                    FROM jobs
                    WHERE url IS NOT NULL AND url_hash IS NULL
                    ORDER BY job_id
                    LIMIT :n
                """), {"n": BATCH}).fetchall()
            else:
                rows = db.execute(text("""
                    SELECT job_id, url
                    FROM jobs
                    WHERE url IS NOT NULL AND url_hash IS NULL AND job_id > :last
                    ORDER BY job_id
                    LIMIT :n
                """), {"n": BATCH, "last": str(last_id)}).fetchall()

            if not rows:
                break

            updated = skipped = 0
            for job_id, url in rows:
                last_id = job_id  # advance cursor no matter what

                canon = canonicalize_url(url or "")
                uh = sha256_bytes(canon) if canon else None
                if not uh:
                    skipped += 1
                    continue

                # If another row already has this url_hash, skip to avoid UNIQUE violation
                exists = db.execute(text("""
                    SELECT 1
                    FROM jobs
                    WHERE url_hash = :uh AND job_id <> :id
                    LIMIT 1
                """), {"uh": uh, "id": str(job_id)}).fetchone()

                if exists:
                    skipped += 1
                    continue

                db.execute(text("""
                    UPDATE jobs
                    SET url_hash = :uh
                    WHERE job_id = :id AND url_hash IS NULL
                """), {"uh": uh, "id": str(job_id)})
                updated += 1

            db.commit()
            print(f"Updated {updated}, skipped {skipped} (batch size {len(rows)})")

        # Optional: merge true duplicates (keep newest)
        if merge_duplicates:
            db.execute(text("""
                WITH ranked AS (
                  SELECT job_id, url_hash, created_at,
                         ROW_NUMBER() OVER (
                           PARTITION BY url_hash
                           ORDER BY created_at DESC, job_id DESC
                         ) AS rn
                  FROM jobs
                  WHERE url_hash IS NOT NULL
                ),
                to_delete AS (SELECT job_id FROM ranked WHERE rn > 1)
                DELETE FROM jobs j
                USING to_delete d
                WHERE j.job_id = d.job_id
            """))
            db.commit()
            print("Merged duplicate rows by url_hash (kept newest per hash).")

        # Diagnostics (separate queries)
        missing = db.execute(text("""
            SELECT COUNT(*) FROM jobs WHERE url IS NOT NULL AND url_hash IS NULL
        """)).scalar_one()
        dup_groups = db.execute(text("""
            SELECT COUNT(*) FROM (
              SELECT url_hash
              FROM jobs
              WHERE url_hash IS NOT NULL
              GROUP BY url_hash
              HAVING COUNT(*) > 1
            ) x
        """)).scalar_one()

        print(f"Remaining with NULL url_hash: {missing}")
        print(f"Duplicate url_hash groups:   {dup_groups}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--merge-duplicates", action="store_true",
                    help="Keep newest per url_hash and delete the rest after backfill.")
    args = ap.parse_args()
    backfill_url_hash(merge_duplicates=args.merge_duplicates)
