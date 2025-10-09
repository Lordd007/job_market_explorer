# scripts/dbcheck.py
from sqlalchemy import text
from db.session import SessionLocal

CHECKS = {
    "dupe_url_hash": """
        SELECT COUNT(*) FROM (
          SELECT url_hash FROM jobs WHERE url_hash IS NOT NULL
          GROUP BY url_hash HAVING COUNT(*) > 1
        ) x
    """,
    "null_desc_hash_recent": """
        SELECT COUNT(*) FROM jobs
        WHERE created_at >= NOW() - INTERVAL '90 days'
          AND (desc_hash IS NULL)
    """,
}

def main():
    failed = 0
    with SessionLocal() as db:
        for name, sql in CHECKS.items():
            n = db.execute(text(sql)).scalar_one()
            ok = (n == 0)
            print(f"{name}: {n} {'OK' if ok else 'FAIL'}")
            failed += (0 if ok else 1)
    if failed:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
