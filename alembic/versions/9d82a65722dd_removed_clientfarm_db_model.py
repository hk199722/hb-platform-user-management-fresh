"""Removed ClientFarm DB model

Revision ID: 9d82a65722dd
Revises: a183f6a5404a
Create Date: 2022-03-10 16:54:26.681005

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9d82a65722dd"
down_revision = "a183f6a5404a"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("client_farm")


def downgrade():
    op.create_table(
        "client_farm",
        sa.Column("farm_uid", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("client_uid", postgresql.UUID(), autoincrement=False, nullable=True),
        sa.ForeignKeyConstraint(
            ["client_uid"], ["client.uid"], name="client_farm_client_uid_fkey", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("farm_uid", name="client_farm_pkey"),
    )
