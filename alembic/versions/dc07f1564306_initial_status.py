"""Initial status

Revision ID: dc07f1564306
Revises:
Create Date: 2021-11-12 12:24:46.992233

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

# revision identifiers, used by Alembic.
revision = "dc07f1564306"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
    op.create_table(
        "client",
        sa.Column(
            "uid",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("uid"),
    )
    op.create_table(
        "gcp_user",
        sa.Column(
            "uid",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("phone_number", sa.String(length=50), nullable=True),
        sa.Column("roles", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.PrimaryKeyConstraint("uid"),
    )
    op.create_table(
        "client_farm",
        sa.Column("farm_uid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("client_uid", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["client_uid"],
            ["client.uid"],
        ),
        sa.PrimaryKeyConstraint("farm_uid"),
    )
    op.create_table(
        "client_users",
        sa.Column("client_uid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gcp_user_uid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["client_uid"],
            ["client.uid"],
        ),
        sa.ForeignKeyConstraint(
            ["gcp_user_uid"],
            ["gcp_user.uid"],
        ),
        sa.PrimaryKeyConstraint("client_uid", "gcp_user_uid"),
    )


def downgrade():
    op.drop_table("client_users")
    op.drop_table("client_farm")
    op.drop_table("gcp_user")
    op.drop_table("client")
