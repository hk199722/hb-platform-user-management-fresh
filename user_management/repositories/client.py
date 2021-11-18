from user_management.models import Client
from user_management.repositories.base import AlchemyRepository
from user_management.schemas import ClientSchema


class ClientRepository(AlchemyRepository):
    model = Client
    schema = ClientSchema
