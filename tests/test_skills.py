# tests/test_skills.py
import json
from db.models import Skill, Job, JobSkill
from ingest.skills_extract import build_matcher, extract

def test_skill_seed_and_extract(db_session):
    # ensure seeds exist (call seed_skills or insert a couple here)
    if not db_session.query(Skill).count():
        from ingest.seed_skills import run as seed_run
        seed_run()

    build_matcher(db_session)
    text = "We use Python, Pandas, and scikit-learn on Kubernetes."
    hits = dict(extract(text))
    assert "python" in hits
    assert "pandas" in hits
    assert "scikit-learn" in hits
    assert "kubernetes" in hits

def test_link_job_skills(db_session):
    job = Job(title="DS", company="Acme", description_text="Python and SQL with Airflow")
    db_session.add(job); db_session.flush()

    from ingest.skills_extract import build_matcher, extract
    from db.models import Skill, JobSkill
    if not db_session.query(Skill).count():
        from ingest.seed_skills import run as seed_run
        seed_run()
    build_matcher(db_session)

    hits = extract(job.description_text)
    for name, conf in hits:
        sk = db_session.query(Skill).filter_by(name_canonical=name).first()
        db_session.add(JobSkill(job_id=str(job.job_id), skill_id=sk.skill_id, confidence=conf))
    db_session.commit()

    cnt = db_session.query(JobSkill).filter_by(job_id=str(job.job_id)).count()
    assert cnt >= 2
