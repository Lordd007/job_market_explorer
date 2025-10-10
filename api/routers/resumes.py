from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text as sql
from db.session import SessionLocal
from db.models import Resume, ResumeSkill
import uuid, mimetypes, json, datetime

# existing skill extraction
from ingest.skills_extract import build_matcher, extract as extract_skills

# resume text extraction (pdf/docx/txt)
from utils.resume_extract import extract_text_from_file

# NEW: structured parser (contact/experience/education/links)
from utils.resume_parse import parse_resume_text

# NEW: optional embedding (fastembed) -- comment out if you haven't switched yet
from utils.embedder import embed_text

router = APIRouter(tags=["resumes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_id() -> uuid.UUID:
    # MVP: stub a single demo user; replace with real auth later
    return uuid.UUID(int=1)  # deterministic demo UUID

@router.post("/resumes")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    user_id = get_current_user_id()

    #Check to see if user exists in db
    db.execute(sql("""
            INSERT INTO users (user_id, auth_sub, email)
            VALUES (:id, 'demo-user', 'demo@example.com')
            ON CONFLICT (user_id) DO NOTHING
        """), {"id": str(user_id)})


    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "File too large (limit 5MB for demo)")

    # detect mime - prefer UploadFile.content_type; fallback to filename
    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"

    text = extract_text_from_file(file.filename or "resume", mime, content)
    if not text or len(text.strip()) < 30:
        raise HTTPException(400, "Could not extract text from resume")

    # INSERT resumes row
    res = Resume(
        user_id=user_id,
        file_mime=mime,
        file_size=len(content),
        text_content=text[:1_000_000],  # keep within DB limits
    )
    db.add(res)
    db.flush()  # get resume_id

    # ---- OPTIONAL: embed resume text (384-dim fastembed) ----
    try:
        vec = embed_text(text or "")
        db.execute(sql("UPDATE resumes SET embedding=:v WHERE resume_id=:id"), {"v": vec, "id": res.resume_id})
    except Exception:
        # keep the app healthy if embeddings fail; you can log here
        pass

    # ---- ATS-style parsing (contact/summary/experience/education/links) ----
    parsed = parse_resume_text(text or "")
    now = datetime.datetime.now(datetime.timezone.utc)

    # store parsed_at on resumes
    db.execute(sql("UPDATE resumes SET parsed_at=:ts WHERE resume_id=:id"), {"ts": now, "id": res.resume_id})

    # one-to-one parsed fields
    db.execute(sql("""
        INSERT INTO resume_parsed(resume_id, full_name, email, phone, city, region, country, postal_code, summary, years_experience)
        VALUES (:rid, :fn, :em, :ph, :city, :region, :country, :postal, :summary, :yrs)
        ON CONFLICT (resume_id) DO UPDATE
        SET full_name=:fn, email=:em, phone=:ph, city=:city, region=:region, country=:country,
            postal_code=:postal, summary=:summary, years_experience=:yrs
    """), {
        "rid": res.resume_id,
        "fn": parsed.get("contact", {}).get("full_name"),
        "em": parsed.get("contact", {}).get("email"),
        "ph": parsed.get("contact", {}).get("phone"),
        "city": parsed.get("contact", {}).get("city"),
        "region": parsed.get("contact", {}).get("region"),
        "country": parsed.get("contact", {}).get("country"),
        "postal": parsed.get("contact", {}).get("postal_code"),
        "summary": parsed.get("summary"),
        "yrs": parsed.get("years_experience"),
    })

    # links (linkedin, portfolio, github)
    db.execute(sql("DELETE FROM resume_links WHERE resume_id=:rid"), {"rid": res.resume_id})
    for link in parsed.get("links", []):
        if not link.get("url"):
            continue
        db.execute(sql("""
            INSERT INTO resume_links(resume_id, kind, url)
            VALUES (:rid, :kind, :url)
            ON CONFLICT DO NOTHING
        """), {"rid": res.resume_id, "kind": link.get("kind") or "other", "url": link["url"]})

    # experience entries
    db.execute(sql("DELETE FROM resume_experience WHERE resume_id=:rid"), {"rid": res.resume_id})
    for e in parsed.get("experience", []):
        db.execute(sql("""
            INSERT INTO resume_experience(resume_id, title, company, location, start_text, end_text, bullets_json)
            VALUES (:rid, :title, :company, :loc, :start, :end, :bul)
        """), {
            "rid": res.resume_id,
            "title": e.get("title"),
            "company": e.get("company"),
            "loc": e.get("location"),
            "start": e.get("start"),
            "end": e.get("end"),
            "bul": json.dumps(e.get("bullets", [])),
        })

    # education entries
    db.execute(sql("DELETE FROM resume_education WHERE resume_id=:rid"), {"rid": res.resume_id})
    for ed in parsed.get("education", []):
        db.execute(sql("""
            INSERT INTO resume_education(resume_id, degree, school, year)
            VALUES (:rid, :deg, :sch, :yr)
        """), {"rid": res.resume_id, "deg": ed.get("degree"), "sch": ed.get("school"), "yr": ed.get("year")})

    # ---- skills from resume text (dictionary matcher you already have) ----
    build_matcher(db)
    hits = extract_skills(text or "")
    for name, conf in hits:
        db.add(ResumeSkill(resume_id=res.resume_id, skill=name, confidence=conf))

    db.commit()

    return {
        "resume_id": str(res.resume_id),
        "parsed": {
            "full_name": parsed.get("contact", {}).get("full_name"),
            "email": parsed.get("contact", {}).get("email"),
            "phone": parsed.get("contact", {}).get("phone"),
            "city": parsed.get("contact", {}).get("city"),
            "region": parsed.get("contact", {}).get("region"),
            "postal_code": parsed.get("contact", {}).get("postal_code"),
            "summary": parsed.get("summary"),
            "experience_count": len(parsed.get("experience", [])),
            "education_count": len(parsed.get("education", [])),
            "links": parsed.get("links", []),
        },
        "skills": [{"name": n, "confidence": c} for n, c in hits],
    }
