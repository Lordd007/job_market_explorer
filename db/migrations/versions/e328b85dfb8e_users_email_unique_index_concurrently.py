"""users.email unique index (concurrently)

Revision ID: e328b85dfb8e
Revises: 1014_auth_login_codes
Create Date: 2025-10-15 17:12:27.137640

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e328b85dfb8e"
down_revision: Union[str, Sequence[str], None] = "1014_auth_login_codes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Must run outside a transaction for CONCURRENTLY
    with op.get_context().autocommit_block():
        op.create_index(
            "users_email_uq",
            "users",
            ["email"],
            unique=True,
            postgresql_concurrently=True,
        )

def downgrade():
    with op.get_context().autocommit_block():
        op.drop_index(
            "users_email_uq",
            table_name="users",
            postgresql_concurrently=True,
        )