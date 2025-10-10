"""resume_structured_fixed_keyword

Revision ID: ceaa859a377a
Revises: 1b03c99bdd97
Create Date: 2025-10-10 16:32:22.532652

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ceaa859a377a"
down_revision: Union[str, Sequence[str], None] = "1b03c99bdd97"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # these will no-op with a clear error if the names don't exist;
    # if you guarded creation earlier you can wrap in DO $$ blocks.
    try:
        op.execute('ALTER TABLE resume_experience RENAME COLUMN "end" TO end_text')
    except Exception:
        op.execute('ALTER TABLE resume_experience RENAME COLUMN end TO end_text')
    try:
        op.execute('ALTER TABLE resume_experience RENAME COLUMN "start" TO start_text')
    except Exception:
        op.execute('ALTER TABLE resume_experience RENAME COLUMN start TO start_text')

def downgrade():
    try:
        op.execute('ALTER TABLE resume_experience RENAME COLUMN start_text TO "start"')
    except Exception:
        op.execute('ALTER TABLE resume_experience RENAME COLUMN start_text TO start')
    try:
        op.execute('ALTER TABLE resume_experience RENAME COLUMN end_text TO "end"')
    except Exception:
        op.execute('ALTER TABLE resume_experience RENAME COLUMN end_text TO end')