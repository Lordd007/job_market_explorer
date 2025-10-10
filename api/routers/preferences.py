from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import UserPreferences
import uuid
from pydantic import BaseModel, Field
from typing import List, Literal

router = APIRouter(tags=["preferences"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_current_user_id() -> uuid.UUID:
    return uuid.UUID(int=1)

class PrefsIn(BaseModel):
    cities: List[str] = Field(default_factory=list)
    remote_mode: Literal["remote","hybrid","office","any"] = "any"
    target_skills: List[str] = Field(default_factory=list)
    companies: List[str] = Field(default_factory=list)
    seniority: Literal["any","entry","mid","senior"] = "any"

@router.get("/user/preferences")
def get_prefs(db: Session = Depends(get_db)):
    uid = get_current_user_id()
    row = db.get(UserPreferences, uid)
    if not row:
        return PrefsIn().model_dump()
    return {
        "cities": row.cities or [],
        "remote_mode": row.remote_mode,
        "target_skills": row.target_skills or [],
        "companies": row.companies or [],
        "seniority": row.seniority,
    }

@router.put("/user/preferences")
def put_prefs(body: PrefsIn, db: Session = Depends(get_db)):
    uid = get_current_user_id()
    row = db.get(UserPreferences, uid)
    if not row:
        row = UserPreferences(user_id=uid)
        db.add(row)
    row.cities = body.cities
    row.remote_mode = body.remote_mode
    row.target_skills = body.target_skills
    row.companies = body.companies
    row.seniority = body.seniority
    db.commit()
    return {"ok": True}
