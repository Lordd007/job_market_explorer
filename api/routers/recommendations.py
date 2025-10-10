from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from db.session import SessionLocal
from utils.embedder import embed_text
import uuid
from typing import List, Dict, Any

router = APIRouter(tags=["recommendations"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def get_current_user_id() -> uuid.UUID:
    return uuid.UUID(int=1)

def _score_rule(row, prefs):
    score = 0.0
    # boost target skills overlap (if job_skills joined later)
    # boost company preference
    if prefs.get("companies"):
        if row["company"] and row["company"].lower() in [c.lower() for c in prefs["companies"]]:
            score += 0.15
    # (Add more simple rules as you like)
    return score

@router.post("/recommendations")
def recommend(db: Session = Depends(get_db)):
    uid = get_current_user_id()
    # get last resume text embedding
    res = db.execute(text("""
      SELECT r.resume_id, r.embedding, r.text_content
      FROM resumes r
      WHERE r.user_id=:uid
      ORDER BY r.created_at DESC
      LIMIT 1
    """), {"uid": str(uid)}).mappings().first()
    if not res:
        raise HTTPException(400, "No resume found")

    vec = res["embedding"]
    if vec is None:
        vec = embed_text(res["text_content"] or "")
        db.execute(text("UPDATE resumes SET embedding=:v WHERE resume_id=:id"), {"v": vec, "id": res["resume_id"]})
        db.commit()

    # prefs
    prefs = db.execute(text("""
      SELECT cities, remote_mode, target_skills, companies, seniority
      FROM user_preferences WHERE user_id=:uid
    """), {"uid": str(uid)}).mappings().first() or {"cities": [], "remote_mode":"any","target_skills":[],"companies":[],"seniority":"any"}

    # vector search (nearest neighbors), pgvector: <#> cosine distance if normalized
    rows = db.execute(text("""
      SELECT job_id, title, company, city, region, country, posted_at, created_at, url,
             1 - (embedding <#> :v) AS sim
      FROM jobs
      WHERE embedding IS NOT NULL
      ORDER BY embedding <#> :v
      LIMIT 200
    """), {"v": vec}).mappings().all()

    # re-rank with rules
    ranked = []
    for r in rows:
        s = r["sim"] + _score_rule(r, prefs)
        ranked.append((s, r))
    ranked.sort(key=lambda t: t[0], reverse=True)
    top = [r for _, r in ranked[:50]]

    return {
        "items": top,
        "explain": "cosine similarity + small rule boosts (company match, etc.)"
    }
