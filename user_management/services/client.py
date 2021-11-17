from typing import List

from pydantic import UUID4
from sqlalchemy.orm import Session

from user_management.repositories.client import ClientRepository
from user_management.schemas import ClientSchema, NewClientSchema


class ClientService:
    def __init__(self, db: Session):
        self.client_repository = ClientRepository(db)

    def create_client(self, client: NewClientSchema) -> ClientSchema:
        return self.client_repository.create(schema=client)

    def list_clients(self) -> List[ClientSchema]:
        return self.client_repository.list()

    def update_client(self, uid: UUID4, client: NewClientSchema) -> ClientSchema:
        return self.client_repository.update(pk=uid, schema=client)

    def delete_client(self, uid: UUID4) -> None:
        return self.client_repository.delete(pk=uid)
