from user_management.models import GCPUser, ClientUser
from user_management.repositories.base import AlchemyRepository
from user_management.schemas import GCPUserSchema, NewGCPUserSchema


class GCPUserRepository(AlchemyRepository):
    model = GCPUser
    schema = GCPUserSchema

    def create(self, schema: NewGCPUserSchema) -> GCPUserSchema:
        """Overrides base `create` method to handle user roles creation for a given client, via the
        `ClientUser` association object.
        """
        response = super().create(schema=schema)

        if schema.role is not None:
            # User role passed in. Create role for given Client.
            client_user = ClientUser(
                client_uid=schema.role.client_uid, gcp_user_uid=response.uid, role=schema.role.role
            )
            self.db.add(client_user)
            self.db.commit()

            response.clients = [client_user]

        return response
