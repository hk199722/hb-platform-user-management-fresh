from pydantic import UUID4

from user_management.models import GCPUser, ClientUser
from user_management.repositories.base import AlchemyRepository
from user_management.schemas import GCPUserSchema, NewGCPUserSchema


class GCPUserRepository(AlchemyRepository):
    model = GCPUser
    schema = GCPUserSchema

    def _persist_user_role(
        self, schema: NewGCPUserSchema, ready_response: GCPUserSchema
    ) -> GCPUserSchema:
        """Helper method to check up for submitted user roles for a given client."""
        if schema.role is not None:
            # User role passed in. Create role for given Client.
            client_user = ClientUser(
                client_uid=schema.role.client_uid,
                gcp_user_uid=ready_response.uid,
                role=schema.role.role,
            )
            self.db.add(client_user)
            self._persist_changes(schema=schema)
            ready_response.clients = [client_user]

        return ready_response

    def create(self, schema: NewGCPUserSchema) -> GCPUserSchema:
        """Overrides base `create` method to handle user roles creation for a given client"""
        response = super().create(schema=schema)

        return self._persist_user_role(schema=schema, ready_response=response)

    def update(self, pk: UUID4, schema: NewGCPUserSchema) -> GCPUserSchema:
        """Overrides base `update` method to handle user roles modifications for a given client."""
        response = super().update(pk=pk, schema=schema)

        return self._persist_user_role(schema=schema, ready_response=response)
