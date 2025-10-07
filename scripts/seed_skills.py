# scripts/seed_skills.py
from __future__ import annotations
import json
from pathlib import Path
from sqlalchemy import text
from db.session import SessionLocal

def main(path: str = "data/seed_skills.json"):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    UPSERT = """
    INSERT INTO skills(name_canonical, category, aliases_json)
    VALUES(:name, :cat, :aliases)
    ON CONFLICT (name_canonical) DO UPDATE
      SET category = EXCLUDED.category,
          aliases_json = EXCLUDED.aliases_json
    """
    inserted = updated = 0
    with SessionLocal() as db:
        for row in data:
            params = {
                "name": row["name_canonical"].strip(),
                "cat":  row.get("category"),
                "aliases": json.dumps(row.get("aliases", []), ensure_ascii=False),
            }
            # try an update-first to count changed rows, then upsert for safety
            r = db.execute(text("""
                UPDATE skills
                SET category=:cat, aliases_json=:aliases
                WHERE name_canonical=:name
            """), params)
            if r.rowcount == 0:
                db.execute(text(UPSERT), params); inserted += 1
            else:
                updated += 1
        db.commit()
    print(f"Seeded skills → inserted={inserted}, updated={updated}, total={inserted+updated}")

if __name__ == "__main__":
    main()
