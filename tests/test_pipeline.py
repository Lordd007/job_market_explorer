import datetime as dt
from sqlalchemy import func

from db.session import SessionLocal
from db.models import Job, Skill, JobSkill
from ingest.pipeline import save_to_db
from tests.utils import ensure_seed_skills

def test_save_to_db_creates_job_and_skills(db_session):
    #ensure_seed_skills()

    items = [{
        "title": "Data Scientist",
        "company": "Acme",
        "city": "Remote",
        "posted_at": dt.datetime.utcnow(),
        "source": "test_seed",
        "url": "https://example.com/jobs/123",
        "description_text": "We use Python, Pandas, and scikit-learn on Kubernetes.",
    }]

    jobs_before = db_session.query(func.count(Job.job_id)).scalar()
    js_before   = db_session.query(func.count(JobSkill.job_id)).scalar()

    save_to_db(items, db=db_session)  # <- inject the test session

    jobs_after = db_session.query(func.count(Job.job_id)).scalar()
    js_after   = db_session.query(func.count(JobSkill.job_id)).scalar()

    assert jobs_after == jobs_before + 1
    assert js_after > js_before

def test_save_to_db_idempotent_by_url_or_hash(db_session):
    #ensure_seed_skills()

    base = {
        "title": "ML Engineer",
        "company": "Beta Inc",
        "city": "Remote",
        "posted_at": dt.datetime.utcnow(),
        "source": "test_seed",
        "description_text": "Python and SQL with Airflow on Kubernetes.",
    }
    items1 = [{**base, "url": "https://example.com/jobs/777"}]
    items2 = [{**base, "url": "https://example.com/jobs/888"}]  # same content -> same hash

    jobs_before = db_session.query(func.count(Job.job_id)).scalar()

    save_to_db(items1, db=db_session)
    save_to_db(items2, db=db_session)

    jobs_after = db_session.query(func.count(Job.job_id)).scalar()
    assert jobs_after == jobs_before + 1  # deduped by hash
