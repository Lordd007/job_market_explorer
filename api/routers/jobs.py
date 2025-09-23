from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import Job

router = APIRouter(tags=["jobs"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/jobs")
def list_jobs(limit: int = 20, db: Session = Depends(get_db)):
    rows = db.query(Job).order_by(Job.posted_at.desc().nullslast()).limit(limit).all()
    return [
        {
            "job_id": str(r.job_id),
            "title": r.title,
            "company": r.company,
            "city": r.city, "region": r.region, "country": r.country,
            "posted_at": r.posted_at, "url": r.url
        } for r in rows
    ]
