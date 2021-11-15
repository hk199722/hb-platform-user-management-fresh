from fastapi import APIRouter, Depends, status

from user_management.core.dependencies import DBSession, get_database
from user_management.schemas import Client, NewClient
from user_management.services.client import ClientService


router = APIRouter()


@router.post("/clients", status_code=status.HTTP_201_CREATED, response_model=Client)
def create_client(new_client: NewClient, db: DBSession = Depends(get_database)):
    client = ClientService(db).create_client(new_client)
    return client
