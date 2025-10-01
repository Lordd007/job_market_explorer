# api/routers/skills.py
import datetime as dt
from typing import Optional, List
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
    interval_str = f"{weeks * 7} days"

    sql = text(f"""
        WITH base AS (
          SELECT date_trunc('week', COALESCE(j.posted_at, j.created_at))::date AS week, COUNT(*) AS c
          FROM jobs j
          JOIN job_skills js ON js.job_id = j.job_id
          JOIN skills s ON s.skill_id = js.skill_id
          WHERE s.name_canonical = :skill
            AND COALESCE(j.posted_at, j.created_at) >= NOW() - INTERVAL '{interval_str}'
            AND (CAST(:city AS TEXT) IS NULL OR COALESCE(j.city, '') ILIKE :city_like)
          GROUP BY 1
        )
        SELECT week, SUM(c)::int AS cnt
        FROM base
        GROUP BY week
        ORDER BY week
    """)

    rows = db.execute(sql, {
        "skill": skill.lower(),
        "city": city,
        "city_like": f"%{city}%" if city else None,
    }).mappings().all()

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

@router.get("/skills/top")
def top_skills(
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(90, ge=1, le=365),
    city: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    interval_str = f"{days} days"

    sql = text(f"""
        SELECT s.name_canonical AS skill, COUNT(*)::int AS cnt
        FROM job_skills js
        JOIN skills s ON s.skill_id = js.skill_id
        JOIN jobs j ON j.job_id = js.job_id
        WHERE COALESCE(j.posted_at, j.created_at) >= NOW() - INTERVAL '{interval_str}'
          AND (CAST(:city AS TEXT) IS NULL OR COALESCE(j.city, '') ILIKE :city_like)
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT :limit
    """)

    params = {
        "city": city,
        "city_like": f"%{city}%" if city else None,
        "limit": limit
    }
    rows = db.execute(sql, params).mappings().all()
    return list(rows)
