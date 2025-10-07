# db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import get_settings

# DATABASE_URL should look like: postgresql+psycopg://USER:PASS@HOST:5432/DB
settings = get_settings()
if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)
