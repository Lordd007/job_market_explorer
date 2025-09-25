# tests/test_config.py
import os
from core.config import get_settings

def test_settings_reads_env():
    os.environ["DATABASE_URL"] = "postgresql+psycopg://jme:jme@localhost:5432/jme_test"
    s = get_settings()
    assert "postgresql+psycopg://" in s.DATABASE_URL
