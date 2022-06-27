from pydantic import UUID4

from user_management.core.dependencies import DBSession, User
from user_management.core.exceptions import AuthorizationError, ResourceNotFoundError
from user_management.repositories import GCPUserRepository
from user_management.schemas import GCPUserSchema, UpdateGCPUserSchema


class AuthService:
    def __init__(self, db: DBSession):
        self.gcp_user_repository = GCPUserRepository(db)

    def check_staff_permission(self, request_user: User) -> None:
        if not request_user.staff:
            raise ResourceNotFoundError()

    def check_gcp_user_view_allowance(self, request_user: User, uid: UUID4) -> None:
        """Checks if the given `request_user` does have permissions to view a certain `GCPUser`."""
        if request_user.staff or request_user.uid == uid:
            return None

        clients = request_user.roles.keys()
        matching = self.gcp_user_repository.get_matching_clients(gcp_user_uid=uid, clients=clients)
        if not matching:
            raise ResourceNotFoundError()

    def check_gcp_user_edit_allowance(
        self, request_user: User, uid: UUID4, schema: UpdateGCPUserSchema
    ):
        """Checks if the user can perform actions on the details of another user, such as changing
        or deleting them.
        """
        if request_user.uid != uid:
            # Only staff can edit other users
            self.check_staff_permission(request_user)

        if schema.staff:
            # Only staff can promote other users to staff
            self.check_staff_permission(request_user)
            return  # Staff don't have other roles so don't waste time

        if schema.role is None:
            # Only staff can create users with no clients assigned
            self.check_staff_permission(request_user)
            return

        user_to_edit: GCPUserSchema = self.gcp_user_repository.get(uid)
        current_roles = {
            client_user.client_uid: client_user.role for client_user in user_to_edit.clients
        }

        updated_roles = {schema.role.client_uid: schema.role.role}

        if current_roles != updated_roles:
            # The roles have changed, so we need to check if the user has permission to do that
            # TODO: When adding multiple clients to a user check each client individually
            # https://hummingbirdtech.atlassian.net/browse/FRSH-808
            self.check_client_allowance(request_user, schema.role.client_uid)

    def check_gcp_user_delete_allowance(self, request_user: User, uid: UUID4) -> None:
        """Checks if the given `request user` does have permissions to delete another user. Only HB
        Staff users can delete any user. `SUPERUSER`s can delete a user if, and only if, such user
        belongs **only** to the same Client as the `SUPERUSER`. Otherwise, instead of deleting it,
        the `DELETE` action will just remove the user from the Client that the user and the
        `SUPERUSER` have in common.
        """
        if request_user.staff:
            return None

        gcp_user = self.gcp_user_repository.get(pk=uid)
        if len(gcp_user.clients) > 1:
            # Can't delete GCPUser because it belongs to multiple Clients.
            # Instead, delete the selected ClientUser.
            raise AuthorizationError(
                {
                    "message": f"User {gcp_user.uid} belongs to multiple clients and cannot be "
                    f"deleted."
                }
            )
        elif not gcp_user.clients:
            # Can't delete GCPUser because it doesn't belong to any Client, so a regular platform
            # user can't be a SUPERUSER of it.
            raise AuthorizationError(
                {
                    "message": f"User {gcp_user.uid} does not belong to any client related to "
                    f"request user and cannot be deleted."
                }
            )
        else:
            superuser_role = self.gcp_user_repository.get_superuser_role(
                request_user.uid, client_uid=gcp_user.clients[0].client_uid
            )
            if not superuser_role:
                # Can't delete GCPUser because the request user is not a SUPERUSER of its Client.
                raise AuthorizationError(
                    {
                        "message": f"User {gcp_user.uid} cannot be deleted because request user "
                        f"doesn't have permissions."
                    }
                )

    def check_client_allowance(self, request_user: User, client_uid: UUID4) -> None:
        """Checks if the given `request_user` does have permissions to perform changes related to
        `client`, this is, if it is a `Role.SUPERUSER` within that client.
        """
        if request_user.staff:
            return None

        superuser = self.gcp_user_repository.get_superuser_role(
            gcp_user_uid=request_user.uid, client_uid=client_uid
        )
        if not superuser:
            raise ResourceNotFoundError()

    def check_client_member(self, request_user: User, client_uid: UUID4) -> None:
        """Checks if the given `request_user` does have permissions to read `client` data."""
        if request_user.staff:
            return None

        if client_uid not in request_user.roles.keys():
            raise ResourceNotFoundError()
