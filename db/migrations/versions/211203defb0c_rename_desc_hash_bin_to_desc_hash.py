"""rename desc_hash_bin to desc_hash

Revision ID: 211203defb0c
Revises: 3bd4955f955e
Create Date: 2025-10-06 14:47:34.773181

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '211203defb0c'
down_revision: Union[str, Sequence[str], None] = '3bd4955f955e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) drop old index if it existed on legacy TEXT desc_hash
    op.execute("DROP INDEX IF EXISTS jobs_desc_hash_idx")

    # 2) drop legacy TEXT column; rename binary column
    # use batch_alter_table for safety on Postgres + SQLite
    with op.batch_alter_table("jobs") as b:
        # legacy TEXT column may or may not exist (if already removed locally),
        # so guard with TRY/CATCH-like pattern via executing raw SQL first if needed.
        # If you *know* it exists, uncomment the next line:
        b.drop_column("desc_hash")                    # legacy TEXT desc_hash
        b.alter_column(
            "desc_hash_bin",
            new_column_name="desc_hash",
            existing_type=sa.LargeBinary(),
            existing_nullable=True,
        )

    # 3) recreate index on the new binary desc_hash
    op.create_index("jobs_desc_hash_idx", "jobs", ["desc_hash"], unique=False)


def downgrade():
    # No-op (or implement reverse if you truly need it):
    # - add desc_hash TEXT,
    # - copy from binary if desired,
    # - rename desc_hash -> desc_hash_bin,
    # - recreate index on the TEXT column
    pass
