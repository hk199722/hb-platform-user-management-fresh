from typing import List

from pydantic import UUID4

from user_management.core.dependencies import DBSession
from user_management.repositories.gcp_user import GCPUserRepository
from user_management.schemas import GCPUserSchema, NewGCPUserSchema
from user_management.services.gcp_identity import GCPIdentityProviderService


class GCPUserService:
    def __init__(self, db: DBSession):
        self.gcp_user_repository = GCPUserRepository(db)
        self.gcp_identity_service = GCPIdentityProviderService()

    def create_gcp_user(self, gcp_user: NewGCPUserSchema) -> GCPUserSchema:
        """Persists GCPUser in database and synchronizes new user with GCP Identity Platform."""
        created_user = self.gcp_user_repository.create(schema=gcp_user)

        # Synchronize GCP Identity Platform.
        self.gcp_identity_service.sync_gcp_user(gcp_user=created_user)

        return created_user

    def get_gcp_user(self, uid: UUID4) -> GCPUserSchema:
        return self.gcp_user_repository.get(pk=uid)

    def list_gcp_users(self) -> List[GCPUserSchema]:
        return self.gcp_user_repository.list()

    def update_gcp_user(self, uid: UUID4, gcp_user: NewGCPUserSchema) -> GCPUserSchema:
        updated_user = self.gcp_user_repository.update(pk=uid, schema=gcp_user)

        # Synchronize GCP Identity Platform.
        self.gcp_identity_service.sync_gcp_user(gcp_user=updated_user, update=True)

        return updated_user

    def delete_gcp_user(self, uid: UUID4) -> None:
        return self.gcp_user_repository.delete(pk=uid)
