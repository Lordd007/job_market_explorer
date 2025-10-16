"""Add indexes on jobs

Revision ID: a025be194585
Revises: e328b85dfb8e
Create Date: 2025-10-16 13:47:08.804214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a025be194585"
down_revision: Union[str, Sequence[str], None] = "e328b85dfb8e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # pg_trgm (safe if already installed)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # CONCURRENTLY must be autocommit
    with op.get_context().autocommit_block():
        # Case-insensitive equality/prefix lookups
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS jobs_city_idx       ON jobs (lower(city))")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS jobs_region_idx     ON jobs (lower(region))")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS jobs_country_idx    ON jobs (lower(country))")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS jobs_title_lw_idx   ON jobs (lower(title))")
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS jobs_company_lw_idx ON jobs (lower(company))")

        # Order by "most recent" (planner can scan btree backward for DESC)
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS jobs_ts_idx ON jobs ((COALESCE(posted_at, created_at)))")

        # Trigram GIN for contains/ILIKE on description_text
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS jobs_desc_trgm_idx "
            "ON jobs USING gin (lower(description_text) gin_trgm_ops)"
        )

def downgrade():
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS jobs_desc_trgm_idx")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS jobs_ts_idx")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS jobs_company_lw_idx")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS jobs_title_lw_idx")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS jobs_country_idx")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS jobs_region_idx")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS jobs_city_idx")
