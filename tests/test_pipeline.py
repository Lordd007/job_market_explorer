import datetime as dt
from sqlalchemy import func

from db.session import SessionLocal
from db.models import Job, Skill, JobSkill
from ingest.pipeline import save_to_db


def _ensure_seed_skills():
    # Seed skills if empty (so matcher can find hits)
    with SessionLocal() as db:
        if db.query(func.count(Skill.skill_id)).scalar() == 0:
            from ingest.seed_skills import run as seed
            seed()


def test_save_to_db_creates_job_and_skills():
    _ensure_seed_skills()

    items = [
        {
            "title": "Data Scientist",
            "company": "Acme",
            "city": "Remote",
            "posted_at": dt.datetime.utcnow(),
            "source": "test_seed",
            "url": "https://example.com/jobs/123",
            "description_text": "We use Python, Pandas, and scikit-learn on Kubernetes."
        }
    ]

    with SessionLocal() as db:
        # pre-counts
        jobs_before = db.query(func.count(Job.job_id)).scalar()
        js_before = db.query(func.count(JobSkill.job_id)).scalar()

    save_to_db(items)

    with SessionLocal() as db:
        jobs_after = db.query(func.count(Job.job_id)).scalar()
        js_after = db.query(func.count(JobSkill.job_id)).scalar()

        # 1 new job inserted
        assert jobs_after == jobs_before + 1

        # at least a few skills detected/linked
        assert js_after > js_before

        # check specific skills linked
        job = db.query(Job).filter_by(url="https://example.com/jobs/123").first()
        assert job is not None

        skill_names = {
            s.name_canonical
            for s in db.query(Skill)
            .join(JobSkill, JobSkill.skill_id == Skill.skill_id)
            .filter(JobSkill.job_id == str(job.job_id))
            .all()
        }

        # seed_skills.json should include these canonical names
        for expected in ["python", "pandas", "scikit-learn", "kubernetes"]:
            assert expected in skill_names


def test_save_to_db_idempotent_by_url_or_hash():
    _ensure_seed_skills()

    base = {
        "title": "ML Engineer",
        "company": "Beta Inc",
        "city": "Remote",
        "posted_at": dt.datetime.utcnow(),
        "source": "test_seed",
        "description_text": "Python and SQL with Airflow on Kubernetes."
    }

    # First insert (URL A)
    items1 = [{**base, "url": "https://example.com/jobs/777"}]
    # Second insert: same content but different URL -> should dedupe by desc_hash
    items2 = [{**base, "url": "https://example.com/jobs/888"}]

    with SessionLocal() as db:
        jobs_before = db.query(func.count(Job.job_id)).scalar()

    save_to_db(items1)
    save_to_db(items2)

    with SessionLocal() as db:
        jobs_after = db.query(func.count(Job.job_id)).scalar()

        # Only one job should be present (deduped by URL/hash)
        assert jobs_after == jobs_before + 1

        # And it should have linked skills
        job = (
            db.query(Job)
            .filter(Job.company == "Beta Inc")
            .order_by(Job.created_at.desc())
            .first()
        )
        assert job is not None

        js_count = db.query(func.count(JobSkill.job_id)).filter(JobSkill.job_id == str(job.job_id)).scalar()
        assert js_count >= 2  # e.g., python, sql, airflow, kubernetes
