"""Added creation timestamps to SecurityToken

Revision ID: a183f6a5404a
Revises: 72204bdeeeda
Create Date: 2022-02-01 15:20:21.692087

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a183f6a5404a"
down_revision = "72204bdeeeda"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "security_token",
        sa.Column(
            "created", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True
        ),
    )


def downgrade():
    op.drop_column("security_token", "created")
