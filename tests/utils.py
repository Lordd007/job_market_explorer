# tests/utils.py
from sqlalchemy import func
from db.session import SessionLocal
from db.models import Skill
from ingest.seed_skills import run as seed


def ensure_seed_skills() -> None:
    """
    Ensure that the `skills` table is seeded with canonical skills.
    Runs idempotently: if already seeded, does nothing.
    """
    with SessionLocal() as db:
        count = db.query(func.count(Skill.skill_id)).scalar()
        if count == 0:
            seed()
