from typing import List

from pydantic import UUID4

from user_management.core.dependencies import DBSession, User
from user_management.repositories.gcp_user import GCPUserRepository
from user_management.schemas import GCPUserSchema, NewGCPUserSchema, UpdateGCPUserSchema
from user_management.services.auth import AuthService
from user_management.services.gcp_identity import GCPIdentityPlatformService


class GCPUserService:
    def __init__(self, db: DBSession):
        self.auth_service = AuthService(db)
        self.gcp_user_repository = GCPUserRepository(db)
        self.gcp_identity_service = GCPIdentityPlatformService()

    def create_gcp_user(self, gcp_user: NewGCPUserSchema, user: User) -> GCPUserSchema:
        """Persists `GCPUser` in database and synchronizes new user with GCP Identity Platform."""
        if gcp_user.role is not None:
            self.auth_service.check_client_allowance(
                request_user=user, client=gcp_user.role.client_uid
            )
        else:
            self.auth_service.check_staff_permission(request_user=user)

        created_user: GCPUserSchema = self.gcp_user_repository.create(schema=gcp_user)

        # Synchronize GCP Identity Platform.
        self.gcp_identity_service.sync_gcp_user(gcp_user=created_user)

        return created_user

    def get_gcp_user(self, uid: UUID4, user: User) -> GCPUserSchema:
        """Gets `GCPUser`s data from local database."""
        self.auth_service.check_gcp_user_view_allowance(request_user=user, uid=uid)
        gcp_user = self.gcp_user_repository.get(pk=uid)

        return gcp_user

    def list_gcp_users(self, user: User) -> List[GCPUserSchema]:
        """Lists `GCPUser`s data from local database."""
        if user.staff is True:
            return self.gcp_user_repository.list()

        return self.gcp_user_repository.list_restricted(
            clients=[client_uid for client_uid in user.roles.keys()]
        )

    def update_gcp_user(
        self, uid: UUID4, gcp_user: UpdateGCPUserSchema, user: User
    ) -> GCPUserSchema:
        """Updates `GCPUser` data in database and synchronizes it with GCP Identity Platform."""
        self.auth_service.check_gcp_user_edit_allowance(request_user=user, uid=uid, schema=gcp_user)
        updated_user: GCPUserSchema = self.gcp_user_repository.update(pk=uid, schema=gcp_user)

        # Synchronize GCP Identity Platform.
        self.gcp_identity_service.sync_gcp_user(gcp_user=updated_user, update=True)

        return updated_user

    def delete_gcp_user(self, uid: UUID4, user: User) -> None:
        """Deletes `GCPUser` from local database, and also from GCP Identity Platform."""
        self.auth_service.check_gcp_user_delete_allowance(request_user=user, uid=uid)
        self.gcp_identity_service.remove_gcp_user(uid=uid)
        self.gcp_user_repository.delete(pk=uid)

    def delete_gcp_user_role(self, uid: UUID4, client_uid: UUID4, user: User) -> None:
        """Deletes `ClientUser` associative object from local database, given a `GCPUser.uid` and a
        `Client.uid`.
        """
        self.auth_service.check_gcp_user_edit_allowance(request_user=user, uid=uid)
        self.gcp_user_repository.delete_client_user(gcp_user=uid, client=client_uid)
