# tests/conftest.py
import os
import pathlib
from urllib.parse import urlparse
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from alembic import command
from alembic.config import Config as AlembicConfig

from api.main import app
from api.routers.jobs import get_db

# ---------------------------------------------------------------------------
# 🌱 CONFIGURATION
# ---------------------------------------------------------------------------

# Ensure this points to a dedicated test DB
TEST_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://jme:jme@localhost:5432/jme_test",
)

# ---------------------------------------------------------------------------
# ⚙️ ALEMBIC MIGRATIONS
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def alembic_cfg() -> AlembicConfig:
    base_dir = pathlib.Path(__file__).resolve().parent.parent
    alembic_ini_path = base_dir / "alembic.ini"

    cfg = AlembicConfig(str(alembic_ini_path))

    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)

    return cfg

@pytest.fixture(scope="session", autouse=True)
def run_migrations(alembic_cfg):
    u = urlparse(TEST_DB_URL)
    assert u.hostname in {"localhost", "127.0.0.1", "::1", "postgres"}, (
        f"Unsafe host for destructive reset: {u.hostname}"
    )
    assert u.path.endswith("/jme_test"), f"Unsafe DB name for destructive reset: {u.path}"

    engine = create_engine(TEST_DB_URL, future=True)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))

    command.upgrade(alembic_cfg, "head")
    yield
    # Optional teardown
    # command.downgrade(alembic_cfg, "base")

# ---------------------------------------------------------------------------
# 🧪 SQLALCHEMY SESSION & FASTAPI OVERRIDE
# ---------------------------------------------------------------------------

@pytest.fixture()
def db_session():
    """Fresh transaction-scoped Session per test."""
    engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    conn = engine.connect()
    trans = conn.begin()
    session = TestingSessionLocal(bind=conn)

    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()
        engine.dispose()

@pytest.fixture(autouse=True)
def override_fastapi_db_dependency(db_session):
    """Make FastAPI endpoints use the same session as the test."""
    def _get_test_db():
        yield db_session

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()

# ---------------------------------------------------------------------------
# 🧹 PER-TEST DATA CLEANUP
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _clean_jobs_tables(db_session):
    """Clear job-related tables before each test."""
    db_session.execute(text("DELETE FROM job_skills"))
    db_session.execute(text("DELETE FROM jobs"))
    yield

# ---------------------------------------------------------------------------
# 🔁 ONE-TIME SKILL SEEDING
# ---------------------------------------------------------------------------

from tests.utils import ensure_seed_skills

@pytest.fixture(scope="session", autouse=True)
def seed_skills_once():
    """Seed canonical skills once per test session."""
    ensure_seed_skills()
