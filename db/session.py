# db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import get_settings

settings = get_settings()

# DATABASE_URL should look like: postgresql+psycopg://user:pass@host:5432/dbname
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    # echo=True,  # uncomment for SQL debug logs
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,  # optional but handy for APIs
)
