from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import text as sql
from pydantic import BaseModel, Field
from typing import Literal
import uuid
import datetime as dt

from db.session import SessionLocal
from db.models import UserPreferences, User

router = APIRouter(tags=["preferences"])

# ----- DB session dependency ---------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ----- Try real auth first; fall back to demo user for staging ----------------
DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

try:
    # Optional import - if you added API auth
    from api.deps.auth import get_current_user  # type: ignore

    def get_user_id(user: User = Depends(get_current_user)) -> uuid.UUID:
        return user.user_id

except Exception:
    # No auth dependency available, use demo user silently
    def get_user_id() -> uuid.UUID:  # type: ignore
        return DEMO_USER_ID

# ----- Pydantic models ---------------------------------------------------------
class PrefsIn(BaseModel):
    cities: list[str] = Field(default_factory=list)
    remote_mode: Literal["remote", "hybrid", "office", "any"] = "any"
    target_skills: list[str] = Field(default_factory=list)
    companies: list[str] = Field(default_factory=list)
    seniority: Literal["any", "entry", "mid", "senior", "lead", "manager"] = "any"

class PrefsOut(PrefsIn):
    updated_at: dt.datetime | None = None

def _normalize_list(items: list[str]) -> list[str]:
    # trim, lowercase, dedupe while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for raw in items or []:
        s = (raw or "").strip()
        if not s:
            continue
        key = s.lower()
        if key not in seen:
            seen.add(key)
            out.append(s)  # keep original casing for display
    return out

# ----- Queries -----------------------------------------------------------------
@router.get("/user/preferences", response_model=PrefsOut)
def get_prefs(
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_user_id),
):
    row = db.get(UserPreferences, user_id)
    if not row:
        return PrefsOut()  # defaults
    return PrefsOut(
        cities=row.cities or [],
        remote_mode=row.remote_mode or "any",
        target_skills=row.target_skills or [],
        companies=row.companies or [],
        seniority=row.seniority or "any",
        updated_at=getattr(row, "updated_at", None),
    )

@router.post("/user/preferences", response_model=PrefsOut)
@router.put("/user/preferences",  response_model=PrefsOut)
def save_prefs(
    body: PrefsIn,
    db: Session = Depends(get_db),
    user_id: uuid.UUID = Depends(get_user_id),
):
    # normalize inputs
    cities = _normalize_list(body.cities)
    skills = _normalize_list(body.target_skills)
    companies = _normalize_list(body.companies)

    row = db.get(UserPreferences, user_id)
    now = dt.datetime.utcnow()

    if not row:
        row = UserPreferences(
            user_id=user_id,
            cities=cities,
            remote_mode=body.remote_mode,
            target_skills=skills,
            companies=companies,
            seniority=body.seniority,
            updated_at=now,
        )
        db.add(row)
    else:
        row.cities = cities
        row.remote_mode = body.remote_mode
        row.target_skills = skills
        row.companies = companies
        row.seniority = body.seniority
        if hasattr(row, "updated_at"):
            row.updated_at = now

    db.commit()

    return PrefsOut(
        cities=row.cities or [],
        remote_mode=row.remote_mode or "any",
        target_skills=row.target_skills or [],
        companies=row.companies or [],
        seniority=row.seniority or "any",
        updated_at=getattr(row, "updated_at", None),
    )
