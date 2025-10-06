# scripts/sql.py
from __future__ import annotations
import argparse, sys
from sqlalchemy import text
from db.session import SessionLocal  # uses your DATABASE_URL

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sql", help="SQL string to execute")
    ap.add_argument("--file", help="Path to .sql file to execute")
    args = ap.parse_args()

    if not args.sql and not args.file:
        ap.error("Provide --sql or --file")

    sql = args.sql or open(args.file, "r", encoding="utf-8").read()

    with SessionLocal() as db:
        # allow multiple statements separated by ; (simple split)
        stmts = [s.strip() for s in sql.split(";") if s.strip()]
        for s in stmts:
            res = db.execute(text(s))
            try:
                rows = res.fetchall()
                if rows:
                    # pretty-print a few rows
                    cols = res.keys()
                    print(" | ".join(cols))
                    for r in rows[:20]:
                        print(" | ".join(str(x) for x in r))
            except Exception:
                # not a SELECT (e.g., DDL/DML)
                pass
        db.commit()

if __name__ == "__main__":
    sys.exit(main())
