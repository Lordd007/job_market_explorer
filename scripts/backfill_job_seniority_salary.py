from sqlalchemy import text as sql
from db.session import SessionLocal
from utils.seniority import infer_seniority
from utils.salary import normalize_salary

def main(batch=1000):
    db = SessionLocal()
    try:
        rows = db.execute(sql("""
            SELECT job_id, title, salary_min, salary_max, salary_currency, salary_period
            FROM jobs
            WHERE seniority IS NULL OR salary_usd_annual IS NULL
            LIMIT :batch
        """), {"batch": batch}).mappings().all()
        for r in rows:
            sen = infer_seniority(r["title"])
            usd = normalize_salary(r["salary_min"], r["salary_max"], r["salary_currency"], r["salary_period"])
            db.execute(sql("""
                UPDATE jobs
                SET seniority = :sen, salary_usd_annual = :usd
                WHERE job_id = :id
            """), {"sen": sen, "usd": usd, "id": r["job_id"]})
        db.commit()
        print(f"Backfilled {len(rows)} rows.")
    finally:
        db.close()

if __name__ == "__main__":
    main()
