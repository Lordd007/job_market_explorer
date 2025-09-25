# tests/conftest.py
import os
import tempfile
import contextlib

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from alembic import command
from alembic.config import Config as AlembicConfig

from api.main import app
from api.routers.jobs import get_db  # the dependency we override

# Run docker exec -it jme-postgres psql -U jme -d postgres -c "CREATE DATABASE jme_test;" once if it is not created.

TEST_DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://jme:jme@localhost:5432/jme_test",
)

@pytest.fixture(scope="session")
def alembic_cfg() -> AlembicConfig:
    """Alembic config bound to the test database."""
    cfg = AlembicConfig("alembic.ini")
    # force SQLAlchemy URL to our test DB (overrides alembic.ini)
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    return cfg

@pytest.fixture(scope="session", autouse=True)
def run_migrations(alembic_cfg):
    """Upgrade to head once for the test DB."""
    command.upgrade(alembic_cfg, "head")
    yield
    # optionally, drop everything at the end:
    # command.downgrade(alembic_cfg, "base")

@pytest.fixture()
def db_session():
    """Fresh DB Session per test (transaction rolled back)."""
    engine = create_engine(TEST_DB_URL, pool_pre_ping=True)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    connection = engine.connect()
    trans = connection.begin()

    session = TestingSessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        connection.close()
        engine.dispose()

@pytest.fixture(autouse=True)
def override_fastapi_db_dependency(db_session):
    """Use the same transaction/session in FastAPI routes."""
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()
