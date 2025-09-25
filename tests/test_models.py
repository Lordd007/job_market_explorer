# tests/test_models.py
import datetime as dt
from db.models import Job

def test_job_defaults(db_session):
    job = Job(title="Data Scientist", company="Acme")
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert job.remote_flag is False
    assert job.salary_currency == "USD"
    assert job.salary_period == "yearly"
    assert job.city == "N/A"
    assert job.created_at is not None
    assert isinstance(job.created_at, dt.datetime)
