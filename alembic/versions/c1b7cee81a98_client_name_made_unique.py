"""Client.name made unique

Revision ID: c1b7cee81a98
Revises: dc07f1564306
Create Date: 2021-11-12 14:56:48.447516

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "c1b7cee81a98"
down_revision = "dc07f1564306"
branch_labels = None
depends_on = None


def upgrade():
    op.create_unique_constraint("client_name_key", "client", ["name"])


def downgrade():
    op.drop_constraint("client_name_key", "client", type_="unique")
