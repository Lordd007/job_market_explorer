"""skill_weekly

Revision ID: e6335ed4c7cd
Revises: 0001_init_schema
Create Date: 2025-10-09 01:06:41.910182

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e6335ed4c7cd"
down_revision: Union[str, Sequence[str], None] = "0001_init_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "skill_weekly",
        sa.Column("week_date", sa.Date(), nullable=False),
        sa.Column("city", sa.Text(), nullable=True),
        sa.Column("skill_id", sa.Integer(), nullable=False),
        sa.Column("postings", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("week_date", "city", "skill_id"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.skill_id"], ondelete="CASCADE"),
    )
    op.create_index("skill_weekly_skill_idx", "skill_weekly", ["skill_id"], unique=False)
    op.create_index("skill_weekly_week_idx", "skill_weekly", ["week_date"], unique=False)


def downgrade():
    op.drop_index("skill_weekly_week_idx", table_name="skill_weekly")
    op.drop_index("skill_weekly_skill_idx", table_name="skill_weekly")
    op.drop_table("skill_weekly")