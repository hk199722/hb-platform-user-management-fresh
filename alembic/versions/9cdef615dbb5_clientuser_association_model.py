"""ClientUser association model

Revision ID: 9cdef615dbb5
Revises: 35b59a5cb17e
Create Date: 2021-11-22 10:52:35.358901

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9cdef615dbb5"
down_revision = "35b59a5cb17e"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "client_user",
        sa.Column("client_uid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gcp_user_uid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(length=15), nullable=True),
        sa.ForeignKeyConstraint(["client_uid"], ["client.uid"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["gcp_user_uid"], ["gcp_user.uid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("client_uid", "gcp_user_uid"),
    )
    op.drop_table("client_users")


def downgrade():
    op.create_table(
        "client_users",
        sa.Column("client_uid", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.Column("gcp_user_uid", postgresql.UUID(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["client_uid"], ["client.uid"], name="client_users_client_uid_fkey", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["gcp_user_uid"],
            ["gcp_user.uid"],
            name="client_users_gcp_user_uid_fkey",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("client_uid", "gcp_user_uid", name="client_users_pkey"),
    )
    op.drop_table("client_user")
