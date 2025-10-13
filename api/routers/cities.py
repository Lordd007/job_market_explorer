from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import text as sql
from db.session import SessionLocal

router = APIRouter(tags=["cities"])
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

@router.get("/cities")
def list_cities(min_support: int = Query(50, ge=1), db: Session = Depends(get_db)):
    q = """
    SELECT city, COUNT(*)::int AS n
    FROM jobs
    WHERE city IS NOT NULL AND city <> 'N/A'
    GROUP BY city
    HAVING COUNT(*) >= :min_support
    ORDER BY n DESC, city ASC
    LIMIT 300
    """
    return db.execute(sql(q), {"min_support": min_support}).mappings().all()
