# tests/test_build_skill_weekly.py
import datetime as dt

from sqlalchemy import text

from db.models import Job, JobSkill, Skill
from scripts.build_skill_weekly import build_skill_weekly


def test_build_skill_weekly_coalesces_city_to_all(db_session):
    db_session.execute(text("DELETE FROM skill_weekly"))

    skill = db_session.query(Skill).first()
    assert skill is not None

    now = dt.datetime.now(dt.timezone.utc)
    job_null_city = Job(
        title="Data Scientist",
        company="Acme",
        city=None,
        posted_at=now,
        description_text="Python",
    )
    job_na_city = Job(
        title="Data Analyst",
        company="Beta",
        city="N/A",
        posted_at=now,
        description_text="Python",
    )
    db_session.add_all([job_null_city, job_na_city])
    db_session.flush()

    db_session.add_all([
        JobSkill(job_id=job_null_city.job_id, skill_id=skill.skill_id, confidence=0.9),
        JobSkill(job_id=job_na_city.job_id, skill_id=skill.skill_id, confidence=0.9),
    ])
    db_session.commit()

    build_skill_weekly(db_session)

    rows = db_session.execute(
        text(
            """
            SELECT week_date, city, skill_id, postings
            FROM skill_weekly
            WHERE skill_id = :skill_id
            """
        ),
        {"skill_id": skill.skill_id},
    ).mappings().all()

    assert rows
    assert all(row["city"] == "All" for row in rows)
    assert sum(row["postings"] for row in rows) == 2
