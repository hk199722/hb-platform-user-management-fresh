from typing import List

from pydantic import UUID4

from user_management.core.dependencies import DBSession
from user_management.repositories.gcp_user import GCPUserRepository
from user_management.schemas import GCPUserSchema, NewGCPUserSchema


class GCPUserService:
    def __init__(self, db: DBSession):
        self.gcp_user_repository = GCPUserRepository(db)

    def create_gcp_user(self, gcp_user: NewGCPUserSchema) -> GCPUserSchema:
        # TODO: Validate GCPUSer creation against Client.
        # A GCPUser must be always created to belong to some Client.
        return self.gcp_user_repository.create(schema=gcp_user)

    def get_gcp_user(self, uid: UUID4) -> GCPUserSchema:
        return self.gcp_user_repository.get(pk=uid)

    def list_gcp_users(self) -> List[GCPUserSchema]:
        return self.gcp_user_repository.list()
