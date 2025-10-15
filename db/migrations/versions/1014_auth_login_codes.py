"""auth: login codes table"

Revision ID: 1014_auth_login_codes
Revises: ceaa859a377a
Create Date: 2025-10-12 15:58:46.402935

"""

from alembic import op
import sqlalchemy as sa

revision = "1014_auth_login_codes"
down_revision = "b4d85599e005"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "auth_login_code",
        sa.Column("email", sa.Text(), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default="now()", nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
    )
    op.execute("CREATE INDEX IF NOT EXISTS auth_login_code_exp_idx ON auth_login_code (expires_at)")
    op.execute("CREATE INDEX IF NOT EXISTS users_email_idx ON users (email)")

def downgrade():
    op.execute("DROP INDEX IF EXISTS auth_login_code_exp_idx")
    op.drop_table("auth_login_code")
