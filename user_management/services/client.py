from pydantic import UUID4
from sqlalchemy.orm import Session

from user_management.repositories.client import ClientRepository
from user_management.schemas import NewClient


class ClientService:
    def __init__(self, db: Session):
        self.client_repository = ClientRepository(db)

    def create_client(self, client: NewClient):
        return self.client_repository.create(client)

    def delete_client(self, uid: UUID4):
        return self.client_repository.delete(_id=uid)
