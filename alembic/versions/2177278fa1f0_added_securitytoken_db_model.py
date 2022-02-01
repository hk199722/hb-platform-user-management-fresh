"""Added SecurityToken DB model

Revision ID: 2177278fa1f0
Revises: 867335022b05
Create Date: 2022-01-30 21:18:27.302792

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2177278fa1f0"
down_revision = "867335022b05"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "security_token",
        sa.Column(
            "uid",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("gcp_user_uid", postgresql.UUID(as_uuid=True), nullable=True),
        sa.ForeignKeyConstraint(["gcp_user_uid"], ["gcp_user.uid"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("uid"),
        sa.UniqueConstraint("gcp_user_uid"),
    )


def downgrade():
    op.drop_table("security_token")
