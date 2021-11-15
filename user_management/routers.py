from fastapi import APIRouter, Depends

from user_management.core.dependencies import DBSession, get_database
from user_management.schemas import NewClient
from user_management.services.client import ClientService


router = APIRouter()


@router.post("/clients")
def create_client(new_client: NewClient, db: DBSession = Depends(get_database)):
    return ClientService(db).create_client(new_client)
