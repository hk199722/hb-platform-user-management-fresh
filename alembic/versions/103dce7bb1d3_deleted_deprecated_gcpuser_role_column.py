"""Deleted deprecated GCPUser.role column

Revision ID: 103dce7bb1d3
Revises: 9cdef615dbb5
Create Date: 2021-11-22 12:07:00.110913

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "103dce7bb1d3"
down_revision = "9cdef615dbb5"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("gcp_user", "roles")


def downgrade():
    op.add_column(
        "gcp_user",
        sa.Column("roles", postgresql.ARRAY(sa.INTEGER()), autoincrement=False, nullable=True),
    )
