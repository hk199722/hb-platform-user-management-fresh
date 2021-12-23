from typing import Optional

from pydantic import UUID4

from user_management.core.dependencies import DBSession, User
from user_management.core.exceptions import AuthorizationError, ResourceNotFoundError
from user_management.models import Role
from user_management.repositories.gcp_user import GCPUserRepository
from user_management.schemas import UpdateGCPUserSchema


class AuthService:
    def __init__(self, db: DBSession):
        self.gcp_user_repository = GCPUserRepository(db)

    def check_gcp_user_view_allowance(self, request_user: User, uid: UUID4) -> None:
        """Checks if the given `request_user` does have permissions to view a certain `GCPUser`."""
        if request_user.staff or request_user.uid == uid:
            return None

        clients = request_user.roles.keys()
        matching = self.gcp_user_repository.get_matching_clients(gcp_user_uid=uid, clients=clients)
        if not matching:
            raise ResourceNotFoundError()

    def check_gcp_user_edit_allowance(
        self, request_user: User, uid: UUID4, schema: Optional[UpdateGCPUserSchema] = None
    ) -> None:
        """Checks if the user can perform actions on the details of another user, such as changing
        or deleting them.
        """
        if request_user.staff or request_user.uid == uid:
            return None

        superuser_clients = [
            client_uid
            for client_uid, role in request_user.roles.items()
            if role == Role.SUPERUSER.value
        ]
        clients = [client_uid for client_uid, role in request_user.roles.items()]
        superuser_matching = self.gcp_user_repository.get_matching_clients(
            gcp_user_uid=uid, clients=superuser_clients
        )
        if not superuser_matching:
            # Selected user doesn't seem to belong to any Client from which the request user is a
            # SUPERUSER. Check if the selected user is currently being added to a Client in which
            # the request user is a SUPERUSER, which MUST be allowed.
            matching = self.gcp_user_repository.get_matching_clients(
                gcp_user_uid=uid, clients=clients
            )
            if not matching:
                raise ResourceNotFoundError()

            if schema is not None:
                if schema.role is not None and str(schema.role.client_uid) not in superuser_clients:
                    raise ResourceNotFoundError()

    def check_client_allowance(self, request_user: User, client: UUID4) -> None:
        """Checks if the given `request_user` does have permissions to perform changes related to
        `client`, this is, if it is a `Role.SUPERUSER` within that client.
        """
        if request_user.staff:
            return None

        superuser = self.gcp_user_repository.get_superuser_role(
            gcp_user_uid=request_user.uid, client_uid=client
        )
        if not superuser:
            raise AuthorizationError()
