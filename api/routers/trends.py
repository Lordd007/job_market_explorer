from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text as sql
from db.session import SessionLocal

router = APIRouter(tags=["trends"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/skills/rising")
def rising_skills(
    city: str | None = None,
    weeks: int = Query(8, ge=4, le=52),
    baseline_weeks: int = Query(8, ge=2, le=52),
    min_support: int = Query(20, ge=1),
    db: Session = Depends(get_db),
):
    city_filter = "AND sw.city = :city" if city else ""
    q = f"""
    WITH recent AS (
      SELECT s.name_canonical AS skill, SUM(sw.postings)::int AS cnt
      FROM skill_weekly sw
      JOIN skills s ON s.skill_id = sw.skill_id
      WHERE sw.week_date >= (DATE_TRUNC('week', CURRENT_DATE) - INTERVAL :weeks || ' week')
        {city_filter}
      GROUP BY 1
    ),
    base AS (
      SELECT s.name_canonical AS skill, SUM(sw.postings)::int AS cnt
      FROM skill_weekly sw
      JOIN skills s ON s.skill_id = sw.skill_id
      WHERE sw.week_date <  (DATE_TRUNC('week', CURRENT_DATE) - INTERVAL :weeks || ' week')
        AND sw.week_date >= (DATE_TRUNC('week', CURRENT_DATE) - INTERVAL :weeks || ' week' - INTERVAL :base || ' week')
        {city_filter}
      GROUP BY 1
    )
    SELECT COALESCE(r.skill,b.skill) AS skill,
           COALESCE(r.cnt,0)  AS recent_cnt,
           COALESCE(b.cnt,0)  AS base_cnt,
           CASE WHEN COALESCE(b.cnt,0) = 0 THEN NULL
                ELSE ROUND(((COALESCE(r.cnt,0)-b.cnt)::numeric / NULLIF(b.cnt,0)) * 100,1) END AS pct_delta
    FROM recent r
    FULL OUTER JOIN base b ON b.skill = r.skill
    WHERE COALESCE(r.cnt,0) + COALESCE(b.cnt,0) >= :min_support
    ORDER BY pct_delta DESC NULLS LAST, recent_cnt DESC
    LIMIT 50
    """
    rows = db.execute(sql(q), {
        "weeks": weeks, "base": baseline_weeks, "min_support": min_support, "city": city
    }).mappings().all()
    return rows
