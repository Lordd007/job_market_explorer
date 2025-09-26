import json
import datetime as dt
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import Job
from core.hashing import text_hash

def run():
    db: Session = SessionLocal()
    with open("data/seed_jobs.json","r",encoding="utf-8") as f:
        items = json.load(f)
    added = 0
    for it in items:
        h = text_hash(it.get("title"), it.get("company"), it.get("description_text"))
        exists = db.query(Job).filter_by(url=it.get("url")).first()
        if exists: continue
        job = Job(
            title=it["title"], company=it["company"],
            city=it.get("city"), region=it.get("region"), country=it.get("country"),
            posted_at=dt.datetime.fromisoformat(it["posted_at"]) if it.get("posted_at") else None,
            source=it.get("source","seed"), url=it.get("url"),
            description_text=it.get("description_text"),
            desc_hash=h
        )
        db.add(job)
        added += 1
    db.commit()
    print(f"Seeded {added} jobs")

if __name__ == "__main__":
    run()
