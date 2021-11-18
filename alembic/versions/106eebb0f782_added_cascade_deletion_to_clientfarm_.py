"""Added cascade deletion to ClientFarm.client

Revision ID: 106eebb0f782
Revises: 39fbd0489466
Create Date: 2021-11-18 10:27:21.509774

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "106eebb0f782"
down_revision = "39fbd0489466"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("client_farm_client_uid_fkey", "client_farm", type_="foreignkey")
    op.create_foreign_key(
        "client_farm_client_uid_fkey",
        "client_farm",
        "client",
        ["client_uid"],
        ["uid"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("client_farm_client_uid_fkey", "client_farm", type_="foreignkey")
    op.create_foreign_key(
        "client_farm_client_uid_fkey", "client_farm", "client", ["client_uid"], ["uid"]
    )
