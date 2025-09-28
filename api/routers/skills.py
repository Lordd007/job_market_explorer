# api/routers/skills.py
import datetime as dt
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.session import SessionLocal

router = APIRouter(tags=["skills"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/skills/top")
def top_skills(
    limit: int = 20,
    days: int = 90,
    city: Optional[str] = None,
    db: Session = Depends(get_db),
):
    cutoff = dt.datetime.utcnow() - dt.timedelta(days=days)

    base_sql = """
        SELECT s.name_canonical AS skill, COUNT(*)::int AS cnt
        FROM job_skills js
        JOIN skills s ON s.skill_id = js.skill_id
        JOIN jobs j   ON j.job_id = js.job_id
        WHERE COALESCE(j.posted_at::timestamptz, j.created_at::timestamptz) >= (:cutoff)::timestamptz
    """
    params = {"cutoff": cutoff, "limit": limit}

    # Only add the city clause if provided
    if city:
        base_sql += "\n  AND COALESCE(j.city,'') ILIKE :city_like"
        params["city_like"] = f"%{city}%"

    base_sql += "\n  GROUP BY 1\n  ORDER BY 2 DESC\n  LIMIT :limit"

    rows = db.execute(text(base_sql), params).mappings().all()
    return [dict(r) for r in rows]


@router.get("/skills/trends")
def skill_trends(
    skills: Optional[List[str]] = Query(default=None, alias="skills[]"),
    weeks: int = 12,
    city: Optional[str] = None,
    db: Session = Depends(get_db),
):
    cutoff = (dt.date.today() - dt.timedelta(weeks=weeks - 1))

    base_sql = """
        WITH j2 AS (
            SELECT
                j.job_id AS job_id,
                DATE_TRUNC('week', COALESCE(j.posted_at::timestamptz, j.created_at::timestamptz))::date AS week,
                COALESCE(j.city,'') AS city
            FROM jobs j
        )
        SELECT
            s.name_canonical AS skill,
            j2.week AS week,
            COUNT(*)::int AS count
        FROM j2
        JOIN job_skills js ON js.job_id = j2.job_id
        JOIN skills s     ON s.skill_id = js.skill_id
        WHERE j2.week >= :cutoff
    """
    params = {"cutoff": cutoff}

    if city:
        base_sql += "\n  AND j2.city ILIKE :city_like"
        params["city_like"] = f"%{city}%"

    if skills:
        base_sql += "\n  AND s.name_canonical = ANY(:skills)"
        params["skills"] = skills

    base_sql += "\n  GROUP BY 1, 2\n  ORDER BY week, skill"

    rows = db.execute(text(base_sql), params).mappings().all()
    return [dict(r) for r in rows]
