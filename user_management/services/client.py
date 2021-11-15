from sqlalchemy.orm import Session

from user_management.repositories.client import ClientRepository
from user_management.schemas import NewClient


class ClientService:
    def __init__(self, db: Session):
        self.client_repository = ClientRepository(db)

    def create_client(self, client: NewClient):
        return self.client_repository.create(client)
