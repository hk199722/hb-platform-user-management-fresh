"""Added Capability DB table and relationship with Client

Revision ID: a0428263f115
Revises: 9d82a65722dd
Create Date: 2022-03-11 10:34:08.677180

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a0428263f115"
down_revision = "9d82a65722dd"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "capability",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "client_capability",
        sa.Column("client_uid", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("capability_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["capability_id"], ["capability.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["client_uid"], ["client.uid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("client_uid", "capability_id"),
    )


def downgrade():
    op.drop_table("client_capability")
    op.drop_table("capability")
