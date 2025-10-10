from sqlalchemy import text
from db.session import SessionLocal
from utils.embedder import embed_text

def main():
    with SessionLocal() as db:
        rows = db.execute(text("SELECT job_id, description_text FROM jobs WHERE embedding IS NULL LIMIT 500")).fetchall()
        for job_id, desc in rows:
            vec = embed_text(desc or "")
            db.execute(text("UPDATE jobs SET embedding=:v WHERE job_id=:id"), {"v": vec, "id": job_id})
        db.commit()
        print(f"Embedded {len(rows)} jobs")

if __name__ == "__main__":
    main()
