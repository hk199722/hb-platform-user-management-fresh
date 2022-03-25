from typing import List

from pydantic import UUID4

from user_management.core.dependencies import DBSession, User
from user_management.repositories import GCPUserRepository
from user_management.repositories import SecurityTokenRepository
from user_management.schemas import (
    CreateSecurityTokenSchema,
    GCPUserSchema,
    NewGCPUserSchema,
    UpdateGCPUserSchema,
)
from user_management.services.auth import AuthService
from user_management.services.gcp_identity import GCPIdentityPlatformService


class GCPUserService:
    def __init__(self, db: DBSession):
        self.auth_service = AuthService(db)
        self.gcp_user_repository = GCPUserRepository(db)
        self.security_token_repository = SecurityTokenRepository(db)
        self.gcp_identity_service = GCPIdentityPlatformService()

    def create_gcp_user(self, gcp_user: NewGCPUserSchema, user: User) -> GCPUserSchema:
        """
        Persists `GCPUser` in database and synchronizes new user with GCP Identity Platform. After
        that, it sends an email to the user with a link to set up its HB Platform password.
        """
        if not gcp_user.role:
            self.auth_service.check_staff_permission(request_user=user)
        else:
            self.auth_service.check_client_allowance(
                request_user=user, client_uid=gcp_user.role.client_uid
            )

        created_user: GCPUserSchema = self.gcp_user_repository.create(schema=gcp_user)

        # Synchronize GCP Identity Platform.
        self.gcp_identity_service.sync_gcp_user(gcp_user=created_user)

        # Create a one-time Security Token to be used to let the user set the password for the first
        # time.
        self.security_token_repository.create(
            schema=CreateSecurityTokenSchema(gcp_user_uid=created_user.uid)
        )

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

    def set_user_password(self, uid: UUID4, token: UUID4, password: str) -> None:
        """Sets up the `GCPUser` password in GCP-IP backend."""
        self.security_token_repository.get(pk={"gcp_user_uid": uid, "uid": token})
        self.gcp_identity_service.set_password(gcp_user_uid=uid, password=password)

        # Delete the security token, since it has been used already.
        self.security_token_repository.delete(pk={"gcp_user_uid": uid, "uid": token})
