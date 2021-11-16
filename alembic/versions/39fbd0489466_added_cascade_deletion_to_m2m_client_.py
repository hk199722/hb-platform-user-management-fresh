"""Added cascade deletion to m2m client_users table.

Revision ID: 39fbd0489466
Revises: c1b7cee81a98
Create Date: 2021-11-16 12:31:48.838424

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "39fbd0489466"
down_revision = "c1b7cee81a98"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("client_users_gcp_user_uid_fkey", "client_users", type_="foreignkey")
    op.drop_constraint("client_users_client_uid_fkey", "client_users", type_="foreignkey")
    op.create_foreign_key(
        "client_users_gcp_user_uid_fkey",
        "client_users",
        "gcp_user",
        ["gcp_user_uid"],
        ["uid"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "client_users_client_uid_fkey",
        "client_users",
        "client",
        ["client_uid"],
        ["uid"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("client_users_gcp_user_uid_fkey", "client_users", type_="foreignkey")
    op.drop_constraint("client_users_client_uid_fkey", "client_users", type_="foreignkey")
    op.create_foreign_key(
        "client_users_client_uid_fkey", "client_users", "client", ["client_uid"], ["uid"]
    )
    op.create_foreign_key(
        "client_users_gcp_user_uid_fkey", "client_users", "gcp_user", ["gcp_user_uid"], ["uid"]
    )
