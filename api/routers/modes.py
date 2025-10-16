# api/routers/modes.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text as sql
from db.session import SessionLocal

router = APIRouter(tags=["modes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/modes")
def modes(
    min_count: int = Query(0, ge=0, le=100000),
    db: Session = Depends(get_db)
):
    """
    Returns counts for { Remote | Hybrid | On-site } from jobs.city text.
    """
    q = sql("""
      WITH src AS (
        SELECT LOWER(COALESCE(city,'')) AS city_l FROM jobs
      ),
      labeled AS (
        SELECT CASE
          WHEN city_l ~ '\\b(remote|distributed|home\\s*based)\\b' THEN 'Remote'
          WHEN city_l ~ '\\bhybrid\\b' THEN 'Hybrid'
          ELSE 'On-site'
        END AS mode
        FROM src
      )
      SELECT mode, COUNT(*)::int AS cnt
      FROM labeled
      GROUP BY mode
      HAVING COUNT(*) >= :min_count
      ORDER BY cnt DESC, mode;
    """)
    rows = db.execute(q, {"min_count": min_count}).mappings().all()
    return [{"mode": r["mode"], "count": r["cnt"]} for r in rows]
