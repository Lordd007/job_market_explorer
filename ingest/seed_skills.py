import json
from sqlalchemy.orm import Session
from db.session import SessionLocal
from db.models import Skill


def run():
    db: Session = SessionLocal()
    items = json.load(open("data/seed_skills.json", "r", encoding="utf-8"))
    added = 0
    for it in items:
        name = it["name_canonical"].strip().lower()
        if not db.query(Skill).filter_by(name_canonical=name).first():
            db.add(Skill(name_canonical=name,
                         category=it.get("category"),
                         aliases_json=json.dumps([a.lower() for a in it.get("aliases", [])])))
            added += 1
    db.commit()
    print(f"Seeded {added} skills")


if __name__ == "__main__":
    run()
