from user_management.models import GCPUser
from user_management.repositories.base import AlchemyRepository
from user_management.schemas import GCPUserSchema


class GCPUserRepository(AlchemyRepository):
    model = GCPUser
    schema = GCPUserSchema
