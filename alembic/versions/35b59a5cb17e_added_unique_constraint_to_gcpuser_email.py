"""Added unique constraint to GCPUser.email

Revision ID: 35b59a5cb17e
Revises: 106eebb0f782
Create Date: 2021-11-18 14:12:50.189756

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "35b59a5cb17e"
down_revision = "106eebb0f782"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("gcp_user_email_key", "gcp_user", ["email"])


def downgrade():
    op.drop_constraint("gcp_user_email_key", "gcp_user", type_="unique")
