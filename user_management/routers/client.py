from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import UUID4

from user_management.core.dependencies import DBSession, get_database
from user_management.schemas import ClientSchema, NewClientSchema
from user_management.services.client import ClientService


router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ClientSchema)
def create_client(new_client: NewClientSchema, db: DBSession = Depends(get_database)):
    return ClientService(db).create_client(new_client)


@router.get("/{uid}", response_model=ClientSchema)
def get_client(uid: UUID4, db: DBSession = Depends(get_database)):
    return ClientService(db).get_client(uid=uid)


@router.get("", response_model=List[ClientSchema])
def list_clients(db: DBSession = Depends(get_database)):
    return ClientService(db).list_clients()


@router.patch("/{uid}", response_model=ClientSchema)
def update_client(uid: UUID4, client: NewClientSchema, db: DBSession = Depends(get_database)):
    return ClientService(db).update_client(uid=uid, client=client)


@router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(uid: UUID4, db: DBSession = Depends(get_database)):
    return ClientService(db).delete_client(uid=uid)
