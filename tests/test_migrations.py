# tests/test_migrations.py
from alembic.script import ScriptDirectory
from alembic.config import Config as AlembicConfig

def test_alembic_head_exists():
    cfg = AlembicConfig("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    head = script.get_current_head()
    assert head is not None
