from user_management.core.dependencies import DBSession
from user_management.repositories.gcp_user import GCPUserRepository
from user_management.schemas import GCPUserSchema, NewGCPUserSchema


class GCPUserService:
    def __init__(self, db: DBSession):
        self.gcp_user_repository = GCPUserRepository(db)

    def create_gcp_user(self, gcp_user: NewGCPUserSchema) -> GCPUserSchema:
        return self.gcp_user_repository.create(schema=gcp_user)
