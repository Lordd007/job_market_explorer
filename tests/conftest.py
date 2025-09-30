# tests/conftest.py
import os
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from alembic import command
from alembic.config import Config as AlembicConfig

from api.main import app
from api.routers.jobs import get_db

# Make sure this points at your *test* DB (pytest-env can also set it)
TEST_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://jme:jme@localhost:5432/jme_test",
)

# --- Alembic setup (once per session) ---------------------------------------

@pytest.fixture(scope="session")
def alembic_cfg() -> AlembicConfig:
    cfg = AlembicConfig("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)  # force test DB
    return cfg

@pytest.fixture(scope="session", autouse=True)
def run_migrations(alembic_cfg):
    command.upgrade(alembic_cfg, "head")
    yield
    # command.downgrade(alembic_cfg, "base")  # optional

# --- Session / dependency override ------------------------------------------

@pytest.fixture()
def db_session():
    """Fresh transaction-scoped Session per test."""
    engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    conn = engine.connect()
    trans = conn.begin()                # outer transaction
    session = TestingSessionLocal(bind=conn)

    try:
        yield session
    finally:
        session.close()
        trans.rollback()                # revert all test changes
        conn.close()
        engine.dispose()

@pytest.fixture(autouse=True)
def override_fastapi_db_dependency(db_session):
    """Make FastAPI endpoints use the same session/transaction as the test."""
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()

# --- Per-test cleanup so tests start empty ----------------------------------

@pytest.fixture(autouse=True)
def _clean_jobs_tables(db_session):
    """Empty jobs tables before each test (within the test transaction)."""
    # Order matters due to FKs
    db_session.execute(text("DELETE FROM job_skills"))
    db_session.execute(text("DELETE FROM jobs"))
    # no commit: we stay inside the test transaction
    yield


from tests.utils import ensure_seed_skills

@pytest.fixture(scope="session", autouse=True)
def seed_skills_once():
    """
    Seed canonical skills exactly once for the whole test session.
    Relies on DATABASE_URL pointing at the test DB (via pytest-env).
    """
    ensure_seed_skills()