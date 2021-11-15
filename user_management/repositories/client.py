from user_management.models import Client
from user_management.repositories.base import AlchemyRepository


class ClientRepository(AlchemyRepository):
    model = Client
