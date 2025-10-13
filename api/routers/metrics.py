from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text as sql
from db.session import SessionLocal

router = APIRouter(tags=["metrics"])
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/metrics/salary_by_skill")
def salary_by_skill(skill: str, city: str|None=None, db: Session=Depends(get_db)):
    cf = "AND j.city = :city" if city else ""
    q = f"""
    SELECT PERCENTILE_DISC(0.25) WITHIN GROUP (ORDER BY salary_usd_annual) AS p25,
           PERCENTILE_DISC(0.5)  WITHIN GROUP (ORDER BY salary_usd_annual) AS median,
           PERCENTILE_DISC(0.75) WITHIN GROUP (ORDER BY salary_usd_annual) AS p75,
           COUNT(*)::int AS n
    FROM jobs j
    JOIN job_skills js USING (job_id)
    JOIN skills s ON s.skill_id = js.skill_id
    WHERE j.salary_usd_annual IS NOT NULL
      AND s.name_canonical = :skill
      {cf}
    """
    row = db.execute(sql(q), {"skill": skill, "city": city}).mappings().first()
    return row or {"p25": None, "median": None, "p75": None, "n": 0}
