from pydantic import UUID4

from user_management.core.dependencies import DBSession, User
from user_management.core.exceptions import ResourceNotFoundError
from user_management.repositories.gcp_user import GCPUserRepository


class AuthService:
    def __init__(self, db: DBSession):
        self.gcp_user_repository = GCPUserRepository(db)

    def check_gcp_user_allowance(self, user: User, gcp_user: UUID4) -> None:
        if user.staff:
            return None

        clients = user.roles.keys()
        if not self.gcp_user_repository.get_matching_clients(gcp_user=gcp_user, clients=clients):
            raise ResourceNotFoundError()
