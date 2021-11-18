from typing import List

from pydantic import UUID4

from user_management.core.dependencies import DBSession
from user_management.repositories.client_farm import ClientFarmRepository
from user_management.schemas import ClientFarmSchema


class ClientFarmService:
    def __init__(self, db: DBSession):
        self.client_farm_repository = ClientFarmRepository(db)

    def create_client_farm(self, client_farm: ClientFarmSchema) -> ClientFarmSchema:
        return self.client_farm_repository.create(schema=client_farm)

    def get_client_farm(self, farm_uid: UUID4) -> ClientFarmSchema:
        return self.client_farm_repository.get(pk=farm_uid)

    def list_client_farms(self) -> List[ClientFarmSchema]:
        return self.client_farm_repository.list()
