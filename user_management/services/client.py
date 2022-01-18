from typing import List

from pydantic import UUID4

from user_management.core.dependencies import DBSession, User
from user_management.repositories.client import ClientRepository
from user_management.schemas import ClientSchema, NewClientSchema
from user_management.services.gcp_identity import GCPIdentityPlatformService


class ClientService:
    def __init__(self, db: DBSession):
        self.client_repository = ClientRepository(db)
        self.gcp_identity_service = GCPIdentityPlatformService()

    def create_client(self, client: NewClientSchema) -> ClientSchema:
        return self.client_repository.create(schema=client)

    def get_client(self, uid: UUID4) -> ClientSchema:
        return self.client_repository.get(pk=uid)

    def list_clients(self, user: User) -> List[ClientSchema]:
        if user.staff is True:
            return self.client_repository.list()

        return self.client_repository.list_restricted(user=user)

    def update_client(self, uid: UUID4, client: NewClientSchema) -> ClientSchema:
        return self.client_repository.update(pk=uid, schema=client)

    def delete_client(self, uid: UUID4) -> None:
        """Deletes the `Client` selected by its UUID, making sure that its users are also cleaned up
        from database and GCP-IP remote backend, except those users that are also assigned to other
        clients as well.
        """
        deleted_users = self.client_repository.delete_client_only_users(uid=uid)
        self.gcp_identity_service.remove_bulk_gcp_users(uids=deleted_users)
        return self.client_repository.delete(pk=uid)
