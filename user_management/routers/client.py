from typing import List

from fastapi import APIRouter, Depends, Response, status
from pydantic import UUID4

from user_management.core.dependencies import DBSession, get_database, staff_check, User, user_check
from user_management.schemas import (
    APITokenSchema,
    ClientAPITokenSchema,
    ClientSchema,
    NewNamedEntitySchema,
    VerifiedAPITokenSchema,
)
from user_management.services.client import ClientService


router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ClientSchema)
async def create_client(
    new_client: NewNamedEntitySchema,
    user: User = Depends(staff_check),  # pylint: disable=unused-argument
    db: DBSession = Depends(get_database),
):
    return ClientService(db).create_client(client=new_client)


@router.get("/{uid}", response_model=ClientSchema)
async def get_client(
    uid: UUID4, user: User = Depends(user_check), db: DBSession = Depends(get_database)
):
    return ClientService(db).get_client(uid=uid, user=user)


@router.get("", response_model=List[ClientSchema])
async def list_clients(user: User = Depends(user_check), db: DBSession = Depends(get_database)):
    return ClientService(db).list_clients(user=user)


@router.patch("/{uid}", response_model=ClientSchema)
async def update_client(
    uid: UUID4,
    client: NewNamedEntitySchema,
    user: User = Depends(staff_check),  # pylint: disable=unused-argument
    db: DBSession = Depends(get_database),
):
    return ClientService(db).update_client(uid=uid, client=client)


@router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_client(
    uid: UUID4,
    user: User = Depends(staff_check),  # pylint: disable=unused-argument
    db: DBSession = Depends(get_database),
):
    return ClientService(db).delete_client(uid=uid)


@router.get("/{uid}/api-token", response_model=ClientAPITokenSchema)
async def generate_api_token(
    uid: UUID4,
    user: User = Depends(user_check),
    db: DBSession = Depends(get_database),
):
    return ClientService(db).generate_api_token(uid=uid, user=user)


@router.post("/api-token/verify", response_model=VerifiedAPITokenSchema)
async def verify_api_token(payload: APITokenSchema, db: DBSession = Depends(get_database)):
    return ClientService(db).verify_api_token(payload=payload)
