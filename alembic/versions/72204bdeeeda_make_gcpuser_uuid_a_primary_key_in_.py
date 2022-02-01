"""Make GCPUser UUID a primary key in SecurityToken table

Revision ID: 72204bdeeeda
Revises: 2177278fa1f0
Create Date: 2022-02-01 10:25:41.210560

"""
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "72204bdeeeda"
down_revision = "2177278fa1f0"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "security_token", "gcp_user_uid", existing_type=postgresql.UUID(), nullable=False
    )
    op.drop_constraint("security_token_gcp_user_uid_key", "security_token", type_="unique")


def downgrade():
    op.create_unique_constraint(
        "security_token_gcp_user_uid_key", "security_token", ["gcp_user_uid"]
    )
    op.alter_column(
        "security_token", "gcp_user_uid", existing_type=postgresql.UUID(), nullable=True
    )
