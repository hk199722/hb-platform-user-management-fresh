from user_management.models import SecurityToken
from user_management.repositories.base import AlchemyRepository
from user_management.schemas import SecurityTokenSchema


class SecurityTokenRepository(AlchemyRepository):
    model = SecurityToken
    schema = SecurityTokenSchema
