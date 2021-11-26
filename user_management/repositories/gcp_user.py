from pydantic import BaseModel, UUID4

from user_management.models import GCPUser, ClientUser
from user_management.repositories.base import AlchemyRepository, Schema
from user_management.schemas import ClientUserSchema, GCPUserSchema


class GCPUserRepository(AlchemyRepository):
    model = GCPUser
    schema = GCPUserSchema

    def _persist_user_role(self, schema: BaseModel, ready_response: GCPUserSchema):
        """Helper method to check up for submitted user roles for a given client."""
        role: ClientUserSchema = getattr(schema, "role", None)
        if role is not None:
            # User role passed in. Create role for given Client.
            client_user = ClientUser(
                client_uid=role.client_uid,
                gcp_user_uid=ready_response.uid,
                role=role.role,
            )
            self.db.add(client_user)
            self._persist_changes(schema=schema)
            ready_response.clients = [client_user]

        return ready_response

    def create(self, schema: BaseModel) -> Schema:
        """Overrides base `create` method to handle user roles creation for a given client"""
        response = super().create(schema=schema)

        return self._persist_user_role(schema=schema, ready_response=response)

    def update(self, pk: UUID4, schema: BaseModel) -> Schema:
        """Overrides base `update` method to handle user roles modifications for a given client."""
        response = super().update(pk=pk, schema=schema)

        return self._persist_user_role(schema=schema, ready_response=response)
