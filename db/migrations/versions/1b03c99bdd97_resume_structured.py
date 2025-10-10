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
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = {c['name'] for c in insp.get_columns('resumes')}
    tables = set(insp.get_table_names(schema='public'))

    # --- resumes: parsed_at + embedding (384) ---
    if "parsed_at" not in cols:
        op.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS parsed_at timestamptz")

    if "embedding" not in cols:
        # add fresh at 384-dim
        op.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS embedding vector(384)")
    else:
        # try to coerce to 384 if it exists with a different dim; swallow errors safely
        op.execute("""
        DO $$
        BEGIN
            BEGIN
                ALTER TABLE resumes ALTER COLUMN embedding TYPE vector(384);
            EXCEPTION WHEN others THEN
                -- leave as-is if incompatible; you can adjust manually later
                NULL;
            END;
        END $$;
        """)

    # --- resume_parsed ---
    if "resume_parsed" not in tables:
        op.create_table(
            "resume_parsed",
            sa.Column("resume_id", sa.UUID(as_uuid=True), primary_key=True),
            sa.Column("full_name", sa.Text()),
            sa.Column("email", sa.Text()),
            sa.Column("phone", sa.Text()),
            sa.Column("city", sa.Text()),
            sa.Column("region", sa.Text()),
            sa.Column("country", sa.Text()),
            sa.Column("postal_code", sa.Text()),
            sa.Column("summary", sa.Text()),
            sa.Column("years_experience", sa.Float()),
            sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
        )

    # --- resume_links ---
    if "resume_links" not in tables:
        op.create_table(
            "resume_links",
            sa.Column("resume_id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("kind", sa.Text(), nullable=False),
            sa.Column("url", sa.Text(), nullable=False),
            sa.PrimaryKeyConstraint("resume_id", "kind", "url"),
            sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
        )

    # --- resume_experience ---
    if "resume_experience" not in tables:
        op.create_table(
            "resume_experience",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("resume_id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("title", sa.Text()),
            sa.Column("company", sa.Text()),
            sa.Column("location", sa.Text()),
            sa.Column("start", sa.Text()),
            sa.Column("end", sa.Text()),
            sa.Column("bullets_json", sa.Text(), server_default="[]"),
            sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
        )
        op.execute("CREATE INDEX IF NOT EXISTS resume_exp_resume_idx ON resume_experience (resume_id)")

    # --- resume_education ---
    if "resume_education" not in tables:
        op.create_table(
            "resume_education",
            sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
            sa.Column("resume_id", sa.UUID(as_uuid=True), nullable=False),
            sa.Column("degree", sa.Text()),
            sa.Column("school", sa.Text()),
            sa.Column("year", sa.Text()),
            sa.ForeignKeyConstraint(["resume_id"], ["resumes.resume_id"], ondelete="CASCADE"),
        )
        op.execute("CREATE INDEX IF NOT EXISTS resume_edu_resume_idx ON resume_education (resume_id)")

def downgrade():
    # minimal downgrade (optional)
    op.execute("DROP TABLE IF EXISTS resume_education CASCADE")
    op.execute("DROP TABLE IF EXISTS resume_experience CASCADE")
    op.execute("DROP TABLE IF EXISTS resume_links CASCADE")
    op.execute("DROP TABLE IF EXISTS resume_parsed CASCADE")