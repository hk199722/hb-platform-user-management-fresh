from typing import List

from pydantic import UUID4

from user_management.core.dependencies import DBSession
from user_management.repositories.gcp_user import GCPUserRepository
from user_management.schemas import GCPUserSchema, NewGCPUserSchema
from user_management.services.gcp_identity import GCPIdentityPlatformService


class GCPUserService:
    def __init__(self, db: DBSession):
        self.gcp_user_repository = GCPUserRepository(db)
        self.gcp_identity_service = GCPIdentityPlatformService()

    def create_gcp_user(self, gcp_user: NewGCPUserSchema) -> GCPUserSchema:
        """Persists `GCPUser` in database and synchronizes new user with GCP Identity Platform."""
        created_user: GCPUserSchema = self.gcp_user_repository.create(schema=gcp_user)

        # Synchronize GCP Identity Platform.
        self.gcp_identity_service.sync_gcp_user(gcp_user=created_user)

        return created_user

    def get_gcp_user(self, uid: UUID4) -> GCPUserSchema:
        """Gets `GCPUser`s data from local database."""
        return self.gcp_user_repository.get(pk=uid)

    def list_gcp_users(self) -> List[GCPUserSchema]:
        """Lists `GCPUser`s data from local database."""
        return self.gcp_user_repository.list()

    def update_gcp_user(self, uid: UUID4, gcp_user: NewGCPUserSchema) -> GCPUserSchema:
        """Updates `GCPUser` data in database and synchronizes it with GCP Identity Platform."""
        updated_user: GCPUserSchema = self.gcp_user_repository.update(pk=uid, schema=gcp_user)

        # Synchronize GCP Identity Platform.
        self.gcp_identity_service.sync_gcp_user(gcp_user=updated_user, update=True)

        return updated_user

    def delete_gcp_user(self, uid: UUID4) -> None:
        """Deletes `GCPUser` from local database, and also from GCP Identity Platform."""
        self.gcp_identity_service.remove_gcp_user(uid=uid)
        self.gcp_user_repository.delete(pk=uid)

    def delete_gcp_user_role(self, uid: UUID4, client_uid: UUID4) -> None:
        """Deletes `ClientUser` associative object from local database, given a `GCPUser.uid` and a
        `Client.uid`.
        """
        self.gcp_user_repository.delete_client_user(gcp_user=uid, client=client_uid)
