"""Added 'staff' boolean column to GCPUser to identify HB Staff members.

Revision ID: 867335022b05
Revises: 7b1549b6bf76
Create Date: 2021-12-15 11:07:29.322733

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "867335022b05"
down_revision = "7b1549b6bf76"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("gcp_user", sa.Column("staff", sa.Boolean(), nullable=False))


def downgrade():
    op.drop_column("gcp_user", "staff")
