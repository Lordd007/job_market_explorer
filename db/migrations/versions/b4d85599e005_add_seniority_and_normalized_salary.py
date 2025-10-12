"""add seniority and normalized salary

Revision ID: b4d85599e005
Revises: ceaa859a377a
Create Date: 2025-10-12 15:58:46.402935

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b4d85599e005"
down_revision: Union[str, Sequence[str], None] = "ceaa859a377a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    with op.batch_alter_table("jobs") as b:
        b.add_column(sa.Column("seniority", sa.Text(), nullable=True))
        b.add_column(sa.Column("salary_usd_annual", sa.Numeric(), nullable=True))
    op.execute("CREATE INDEX IF NOT EXISTS jobs_seniority_idx ON jobs (seniority)")
    op.execute("CREATE INDEX IF NOT EXISTS jobs_salary_usd_idx ON jobs (salary_usd_annual)")

def downgrade():
    op.execute("DROP INDEX IF EXISTS jobs_salary_usd_idx")
    op.execute("DROP INDEX IF EXISTS jobs_seniority_idx")
    with op.batch_alter_table("jobs") as b:
        b.drop_column("salary_usd_annual")
        b.drop_column("seniority")
