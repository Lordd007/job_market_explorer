# api/routers/trends.py
from fastapi import APIRouter, Depends, HTTPException, Query
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
    weeks: int = Query(8, ge=1, le=26),
    baseline_weeks: int = Query(8, ge=1, le=26),
    min_support: int = Query(20, ge=0, le=100000),
    limit: int = Query(20, ge=1, le=200),
    city: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Compares the last `weeks` vs the preceding `baseline_weeks`.
    If `city` is provided, restrict to that city label stored in skill_weekly.city.
    """
    # WHERE snippets depending on city
    city_cond = "AND city = :city" if city else ""
    params = {
        "weeks": weeks,
        "baseline_weeks": baseline_weeks,
        "min_support": min_support,
        "limit": limit,
    }
    if city:
        params["city"] = city

    q = sql(f"""
    WITH cur AS (
      SELECT skill_id, SUM(postings)::int AS n
      FROM skill_weekly
      WHERE week_date >= date_trunc('week', now()::date) - (:weeks || ' weeks')::interval
        {city_cond}
      GROUP BY skill_id
    ),
    base AS (
      SELECT skill_id, SUM(postings)::int AS n
      FROM skill_weekly
      WHERE week_date >= date_trunc('week', now()::date) - ((:weeks + :baseline_weeks) || ' weeks')::interval
        AND week_date <  date_trunc('week', now()::date) - (:weeks || ' weeks')::interval
        {city_cond}
      GROUP BY skill_id
    )
    SELECT s.name_canonical AS skill,
           COALESCE(cur.n, 0) AS cur_n,
           COALESCE(base.n, 0) AS base_n,
           /* if base==0 and cur>=min_support call it a huge delta, else compute % change */
           CASE WHEN COALESCE(base.n,0)=0
                    THEN CASE WHEN COALESCE(cur.n,0)>=:min_support THEN 9999.0 ELSE 0.0 END
                ELSE (cur.n - base.n)::float / base.n
           END AS delta,
           COALESCE(cur.n,0) + COALESCE(base.n,0) AS support
    FROM cur
    JOIN skills s ON s.skill_id = cur.skill_id
    LEFT JOIN base ON base.skill_id = cur.skill_id
    WHERE COALESCE(cur.n,0) >= :min_support
    ORDER BY delta DESC, cur_n DESC
    LIMIT :limit;
    """)

    rows = db.execute(q, params).mappings().all()
    # normalize payload
    return [
        {
            "skill": r["skill"],
            "current": int(r["cur_n"]),
            "baseline": int(r["base_n"]),
            "delta": float(r["delta"]),
            "support": int(r["support"]),
        }
        for r in rows
    ]
