# db/migrations/env.py
from __future__ import annotations

from logging.config import fileConfig
from alembic import context
from sqlalchemy import create_engine, pool
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

from db.base import Base
from db import models  # noqa: F401
from core.config import get_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def _with_sslmode_require(url: str, *, env: str) -> str:
    u = urlparse(url)
    if not u.scheme.startswith("postgresql"):
        return url
    q = dict(parse_qsl(u.query))
    hostname = (u.hostname or "").lower()
    if hostname in {"localhost", "127.0.0.1", "::1", "postgres"}:
        q["sslmode"] = "disable"
    elif env.lower() not in {"dev", "test", "local"}:
        q.setdefault("sslmode", "require")
    return urlunparse(u._replace(query=urlencode(q)))

def run_migrations_offline() -> None:
    settings = get_settings()
    url = _with_sslmode_require(settings.DATABASE_URL, env=settings.ENV)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    settings = get_settings()
    url = _with_sslmode_require(settings.DATABASE_URL, env=settings.ENV)
    engine = create_engine(url, poolclass=pool.NullPool, future=True)

    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
