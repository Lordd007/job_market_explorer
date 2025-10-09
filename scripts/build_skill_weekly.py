# scripts/build_skill_weekly.py
from sqlalchemy import text
from db.session import SessionLocal

SQL = """
WITH base AS (
  SELECT date_trunc('week', COALESCE(j.posted_at, j.created_at))::date AS week_date,
         j.city,
         js.skill_id
  FROM jobs j
  JOIN job_skills js ON js.job_id = j.job_id
  WHERE COALESCE(j.posted_at, j.created_at) >= NOW() - INTERVAL '120 days'
)
SELECT week_date, city, skill_id, COUNT(*)::int AS postings
FROM base
GROUP BY 1,2,3
"""

UPSERT = """
INSERT INTO skill_weekly(week_date, city, skill_id, postings)
VALUES (:week_date, :city, :skill_id, :postings)
ON CONFLICT (week_date, city, skill_id)
DO UPDATE SET postings = EXCLUDED.postings
"""

def main():
    with SessionLocal() as db:
        rows = db.execute(text(SQL)).mappings().all()
        for r in rows:
            db.execute(text(UPSERT), r)
        db.commit()
    print(f"Upserted {len(rows)} rows into skill_weekly")

if __name__ == "__main__":
    main()
