"""Changed ClientUser.role to an Enum type

Revision ID: 7b1549b6bf76
Revises: 103dce7bb1d3
Create Date: 2021-11-22 13:25:41.961664

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7b1549b6bf76"
down_revision = "103dce7bb1d3"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("client_user", "role", existing_type=sa.VARCHAR(length=15), nullable=False)


def downgrade():
    op.alter_column("client_user", "role", existing_type=sa.VARCHAR(length=15), nullable=True)
