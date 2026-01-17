"""description of your migration

Revision ID: ca3264475f09
Revises: e6335ed4c7cd
Create Date: 2025-10-09 17:02:31.335344

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ca3264475f09'
down_revision: Union[str, Sequence[str], None] = "e6335ed4c7cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # users
    op.create_table(
        "users",
        sa.Column("user_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("auth_sub", sa.Text(), nullable=False, unique=True),
        sa.Column("email", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # resumes
    op.create_table(
        "resumes",
        sa.Column("resume_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("file_mime", sa.Text(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
    )

    # resume_skills (from your dict matcher)
    op.create_table(
        "resume_skills",
        sa.Column("resume_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("skill", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.9"),
        sa.PrimaryKeyConstraint("resume_id", "skill"),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
    )

    # preferences
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("cities", sa.ARRAY(sa.Text()), server_default="{}", nullable=False),
        sa.Column("remote_mode", sa.Text(), server_default="any", nullable=False),  # remote|hybrid|office|any
        sa.Column("target_skills", sa.ARRAY(sa.Text()), server_default="{}", nullable=False),
        sa.Column("companies", sa.ARRAY(sa.Text()), server_default="{}", nullable=False),
        sa.Column("seniority", sa.Text(), server_default="any", nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"], ondelete="CASCADE"),
    )

def downgrade():
    op.drop_table("user_preferences")
    op.drop_table("resume_skills")
    op.drop_table("resumes")
    op.drop_table("users")
