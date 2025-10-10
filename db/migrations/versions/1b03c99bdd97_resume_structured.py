"""resume_structured

Revision ID: 1b03c99bdd97
Revises: af80da2e077d
Create Date: 2025-10-10 14:01:19.198310

"""
from typing import Sequence, Union
from pgvector.sqlalchemy import Vector
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "1b03c99bdd97"
down_revision: Union[str, Sequence[str], None] = "af80da2e077d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # ensure pgvector exists; resumes.embedding may already exist
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # resumes: add embedding (384) & parsed timestamp if not present
    with op.batch_alter_table("resumes") as b:
        b.add_column(sa.Column("embedding", Vector(dim=384), nullable=True))
        b.add_column(sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True))

    # parsed one-to-one
    op.create_table(
        "resume_parsed",
        sa.Column("resume_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.Text(), nullable=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("phone", sa.Text(), nullable=True),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("region", sa.Text(), nullable=True),   # state/province
        sa.Column("country", sa.Text(), nullable=True),
        sa.Column("postal_code", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("years_experience", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
    )

    # links (linkedin, portfolio, github, etc.)
    op.create_table(
        "resume_links",
        sa.Column("resume_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("kind", sa.Text(), nullable=False),    # linkedin|portfolio|github|other
        sa.Column("url", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("resume_id", "kind", "url"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
    )

    # experience
    op.create_table(
        "resume_experience",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("resume_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("company", sa.Text(), nullable=True),
        sa.Column("location", sa.Text(), nullable=True),
        sa.Column("start", sa.Text(), nullable=True),    # keep as text first; parse later (YYYY-MM)
        sa.Column("end", sa.Text(), nullable=True),      # "Present" allowed
        sa.Column("bullets_json", sa.Text(), server_default="[]"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
    )
    op.create_index("resume_exp_resume_idx", "resume_experience", ["resume_id"])

    # education
    op.create_table(
        "resume_education",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("resume_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("degree", sa.Text(), nullable=True),
        sa.Column("school", sa.Text(), nullable=True),
        sa.Column("year", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
    )
    op.create_index("resume_edu_resume_idx", "resume_education", ["resume_id"])

def downgrade():
    op.drop_index("resume_edu_resume_idx", table_name="resume_education")
    op.drop_table("resume_education")
    op.drop_index("resume_exp_resume_idx", table_name="resume_experience")
    op.drop_table("resume_experience")
    op.drop_table("resume_links")
    op.drop_table("resume_parsed")
