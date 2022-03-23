"""Added ClientAPIToken DB model

Revision ID: 35ce987befa7
Revises: a0428263f115
Create Date: 2022-03-23 16:54:45.648602

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "35ce987befa7"
down_revision = "a0428263f115"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "client_api_token",
        sa.Column("client_uid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(["client_uid"], ["client.uid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("client_uid"),
        sa.UniqueConstraint("token"),
    )


def downgrade():
    op.drop_table("client_api_token")
