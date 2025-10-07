"""init schema (create core tables)"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001_init_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # skills
    op.create_table(
        "skills",
        sa.Column("skill_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name_canonical", sa.Text(), nullable=False, unique=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("aliases_json", sa.Text(), nullable=False, server_default="[]"),
    )

    # jobs
    op.create_table(
        "jobs",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("city", sa.Text(), nullable=True, server_default="N/A"),
        sa.Column("region", sa.Text(), nullable=True, server_default="N/A"),
        sa.Column("country", sa.Text(), nullable=True, server_default="N/A"),
        sa.Column("remote_flag", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("salary_min", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("salary_max", sa.Numeric(), nullable=False, server_default="0"),
        sa.Column("salary_currency", sa.Text(), nullable=False, server_default="USD"),
        sa.Column("salary_period", sa.Text(), nullable=False, server_default="yearly"),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.Text(), nullable=False, server_default="manual"),
        sa.Column("url", sa.String(), nullable=True, unique=True),
        sa.Column("description_text", sa.Text(), nullable=False, server_default=""),
        # FINAL binary hashes
        sa.Column("url_hash", sa.LargeBinary(), nullable=True),
        sa.Column("desc_hash", sa.LargeBinary(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), server_default=sa.text("now()")),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=False),
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("url_hash", name="jobs_url_hash_uq"),
    )
    # index on desc hash
    op.create_index("jobs_desc_hash_idx", "jobs", ["desc_hash"], unique=False)

    # job_skills (many-to-many)
    op.create_table(
        "job_skills",
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.9"),
        sa.Column("source", sa.Text(), nullable=False, server_default="dict_v1"),
        sa.PrimaryKeyConstraint("job_id", "skill_id"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.job_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.skill_id"], ondelete="CASCADE"),
    )
    op.create_index("job_skills_skill_idx", "job_skills", ["skill_id"], unique=False)


def downgrade():
    op.drop_index("job_skills_skill_idx", table_name="job_skills")
    op.drop_table("job_skills")
    op.drop_index("jobs_desc_hash_idx", table_name="jobs")
    op.drop_table("jobs")
    op.drop_table("skills")
