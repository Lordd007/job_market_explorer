# api/routers/skills.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.session import SessionLocal

router = APIRouter(tags=["skills"])

def get_db():
    db = SessionLocal();
    try: yield db
    finally: db.close()

@router.get("/skills/top")
def top_skills(limit: int = 20, db: Session = Depends(get_db)):
    sql = text("""
        SELECT s.name_canonical AS skill, COUNT(*) AS cnt
        FROM job_skills js
        JOIN skills s ON s.skill_id = js.skill_id
        JOIN jobs j ON j.job_id::text = js.job_id
        WHERE j.posted_at IS NULL OR j.posted_at > NOW() - INTERVAL '90 days'
        GROUP BY 1
        ORDER BY 2 DESC
        LIMIT :limit
    """)
    rows = db.execute(sql, {"limit": limit}).mappings().all()
    return rows
