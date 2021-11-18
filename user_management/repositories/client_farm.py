from user_management.models import ClientFarm
from user_management.repositories.base import AlchemyRepository
from user_management.schemas import ClientFarmSchema


class ClientFarmRepository(AlchemyRepository):
    model = ClientFarm
    schema = ClientFarmSchema
