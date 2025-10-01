# api/routers/jobs.py
from fastapi import APIRouter, Depends, Query
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.session import SessionLocal

router = APIRouter(tags=["jobs"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/jobs")
def list_jobs(
    q: Optional[str] = Query(None, description="free text search (title/company/desc)"),
    city: Optional[str] = Query(None),
    skill: Optional[str] = Query(None, description="canonical skill name"),
    days: int = Query(90, ge=1, le=365),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List jobs with filters + pagination. Sort newest first.
    """
    # base WHERE pieces
    interval_str = f"{days} days"

    where = [
        f"COALESCE(j.posted_at::timestamptz, j.created_at::timestamptz) >= NOW() - INTERVAL '{interval_str}'"
    ]
    params: Dict[str, Any] = {}

    if city:
        where.append("COALESCE(j.city,'') ILIKE :city_like")
        params["city_like"] = f"%{city}%"

    if q:
        where.append("(j.title ILIKE :q OR j.company ILIKE :q OR j.description_text ILIKE :q)")
        params["q"] = f"%{q}%"

    join_skill = ""
    if skill:
        join_skill = "JOIN job_skills js ON js.job_id = j.job_id JOIN skills s ON s.skill_id = js.skill_id"
        where.append("s.name_canonical = :skill")
        params["skill"] = skill

    where_sql = " AND ".join(where)
    offset = (page - 1) * page_size

    sql_count = text(f"""
        SELECT COUNT(*)::int AS total
        FROM jobs j
        {join_skill}
        WHERE {where_sql}
    """)
    total = db.execute(sql_count, params).scalar() or 0

    sql_rows = text(f"""
        SELECT
          j.job_id::text, j.title, j.company, j.city, j.region, j.country,
          j.posted_at, j.created_at, j.url
        FROM jobs j
        {join_skill}
        WHERE {where_sql}
        ORDER BY COALESCE(j.posted_at, j.created_at) DESC
        LIMIT :limit OFFSET :offset
    """)
    rows = db.execute(sql_rows, {**params, "limit": page_size, "offset": offset}).mappings().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [dict(r) for r in rows],
    }

@router.get("/skills/suggest")
def suggest_skills(term: str, limit: int = 10, db: Session = Depends(get_db)):
    """
    Typeahead for skills by canonical name or aliases.
    """
    sql = text("""
        SELECT s.name_canonical AS skill, COUNT(*)::int AS cnt
        FROM job_skills js
        JOIN skills s ON s.skill_id = js.skill_id
        WHERE s.name_canonical ILIKE :like
           OR EXISTS (
             SELECT 1 FROM jsonb_array_elements_text((s.aliases_json)::jsonb) a
             WHERE a ILIKE :like
           )
        GROUP BY 1
        ORDER BY cnt DESC
        LIMIT :limit
    """)
    rows = db.execute(sql, {"like": f"%{term}%", "limit": limit}).mappings().all()
    return [r["skill"] for r in rows]
