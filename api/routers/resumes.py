from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import Resume, ResumeSkill, User
import uuid, magic  # file type (python-magic), or fallback to mimetypes
from ingest.skills_extract import build_matcher, extract as extract_skills
from utils.resume_extract import extract_text_from_file

router = APIRouter(tags=["resumes"])

def get_db():
    db = SessionLocal();
    try: yield db
    finally: db.close()

def get_current_user_id() -> uuid.UUID:
    # MVP: stub a single demo user; replace with real auth later
    return uuid.UUID(int=1)  # deterministic demo UUID

@router.post("/resumes")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "File too large (limit 5MB for demo)")

    # detect mime
    try:
        mime = magic.from_buffer(content, mime=True)
    except Exception:
        mime = file.content_type or "application/octet-stream"

    text = extract_text_from_file(file.filename or "resume", mime, content)
    if not text or len(text.strip()) < 30:
        raise HTTPException(400, "Could not extract text from resume")

    res = Resume(
        user_id=user_id,
        file_mime=mime,
        file_size=len(content),
        text_content=text[:1_000_000],  # keep within DB limits
    )
    db.add(res); db.flush()  # get resume_id

    # skills from resume text using existing dictionary/matcher
    build_matcher(db)
    hits = extract_skills(text or "")
    for name, conf in hits:
        db.add(ResumeSkill(resume_id=res.resume_id, skill=name, confidence=conf))
    db.commit()
    return {"resume_id": str(res.resume_id), "skills": [{"name": n, "confidence": c} for n, c in hits]}
