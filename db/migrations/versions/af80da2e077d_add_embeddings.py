"""add_embeddings

Revision ID: af80da2e077d
Revises: ca3264475f09
Create Date: 2025-10-09 17:32:43.413461

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "af80da2e077d"
down_revision: Union[str, Sequence[str], None] = "ca3264475f09"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.add_column("jobs", sa.Column("embedding", Vector(dim=384), nullable=True))
    op.add_column("resumes", sa.Column("embedding", Vector(dim=384), nullable=True))

def downgrade():
    op.drop_column("resumes", "embedding")
    op.drop_column("jobs", "embedding")
