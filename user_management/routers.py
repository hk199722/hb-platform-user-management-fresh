from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import UUID4

from user_management.core.dependencies import DBSession, get_database
from user_management.schemas import Client, NewClient
from user_management.services.client import ClientService


router = APIRouter()


@router.post("/clients", status_code=status.HTTP_201_CREATED, response_model=Client)
def create_client(new_client: NewClient, db: DBSession = Depends(get_database)):
    client = ClientService(db).create_client(new_client)
    return client


@router.get("/clients", response_model=List[Client])
def list_clients(db: DBSession = Depends(get_database)):
    return ClientService(db).list_clients()


@router.patch("/clients/{uid}", response_model=Client)
def update_client(uid: UUID4, client: NewClient, db: DBSession = Depends(get_database)):
    client = ClientService(db).update_client(uid=uid, client=client)
    return client


@router.delete("/clients/{uid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(uid: UUID4, db: DBSession = Depends(get_database)):
    return ClientService(db).delete_client(uid=uid)
