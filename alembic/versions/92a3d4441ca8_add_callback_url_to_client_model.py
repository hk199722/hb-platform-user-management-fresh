"""add callback_url to client model

Revision ID: 92a3d4441ca8
Revises: 35ce987befa7
Create Date: 2022-06-21 08:18:01.870417

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "92a3d4441ca8"
down_revision = "35ce987befa7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("client", sa.Column("callback_url", sa.String(length=255), nullable=True))


def downgrade():
    op.drop_column("client", "callback_url")
