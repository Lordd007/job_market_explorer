# api/routers/skills.py
import datetime as dt
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from db.session import SessionLocal

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.session import SessionLocal

router = APIRouter(tags=["skills"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/skills/trends")
def skill_trends(
    skill: str = Query(..., description="Canonical skill name (e.g. 'python')"),
    weeks: int = Query(12, ge=1, le=52),
    city: Optional[str] = Query(None, description="Optional city filter"),
    db: Session = Depends(get_db),
):
    """
    Weekly counts for a given skill over the last N weeks.
    """
    sql = text("""
        WITH base AS (
          SELECT
            date_trunc('week', COALESCE(j.posted_at, j.created_at))::date AS week,
            1 AS c
          FROM job_skills js
          JOIN jobs j   ON j.job_id = js.job_id
          JOIN skills s ON s.skill_id = js.skill_id
          WHERE s.name_canonical = :skill
            AND COALESCE(j.posted_at::timestamptz, j.created_at::timestamptz)
                  >= NOW() - (:weeks::int * INTERVAL '7 days')
            AND (:city IS NULL OR COALESCE(j.city, '') ILIKE :city_like)
        )
        SELECT week, SUM(c)::int AS cnt
        FROM base
        GROUP BY week
        ORDER BY week
    """)
    rows = db.execute(
        sql,
        {
            "skill": skill,
            "weeks": weeks,
            "city": city,
            "city_like": f"%{city}%" if city else None,
        },
    ).mappings().all()

    # return continuous weeks (fill gaps with 0)
    if not rows:
        return []

    by_week = {r["week"].isoformat(): r["cnt"] for r in rows}
    first = rows[0]["week"]
    last  = rows[-1]["week"]

    out = []
    cur = first
    while cur <= last:
        k = cur.isoformat()
        out.append({"week": k, "cnt": by_week.get(k, 0)})
        cur = (cur + __import__("datetime").timedelta(days=7))
    return out
