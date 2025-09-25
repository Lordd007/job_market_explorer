# tests/test_seed.py
import importlib

def test_seed_is_idempotent(db_session, monkeypatch):
    # Import here so it sees test DB through dependency overrides
    seed_mod = importlib.import_module("ingest.seed_sample")

    # Run twice
    seed_mod.run()
    seed_mod.run()

    # Expect no duplicates by URL (your Job model has unique url)
    from sqlalchemy import func
    from db.models import Job

    total = db_session.query(func.count(Job.job_id)).scalar()
    urls = db_session.query(Job.url).all()

    # If seed URLs are unique, count equals # distinct urls
    distinct_urls = {u[0] for u in urls if u[0]}
    assert total == len(distinct_urls) or len(distinct_urls) == 0
