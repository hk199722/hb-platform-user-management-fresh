from typing import List

from fastapi import APIRouter, Depends, Response, status
from pydantic import UUID4

from user_management.core.dependencies import DBSession, get_database, staff_check, User, user_check
from user_management.schemas import ClientSchema, NewClientSchema
from user_management.services.client import ClientService


router = APIRouter()


# FIXME: Enable Pylint again for the `user` argument once authentication is in place.
# pylint: disable=unused-argument
@router.post("", status_code=status.HTTP_201_CREATED, response_model=ClientSchema)
def create_client(
    new_client: NewClientSchema,
    user: User = Depends(staff_check),  # pylint: disable=unused-argument
    db: DBSession = Depends(get_database),
):
    return ClientService(db).create_client(client=new_client)


@router.get("/{uid}", response_model=ClientSchema)
def get_client(uid: UUID4, user: User = Depends(user_check), db: DBSession = Depends(get_database)):
    return ClientService(db).get_client(uid=uid, user=user)


@router.get("", response_model=List[ClientSchema])
def list_clients(user: User = Depends(user_check), db: DBSession = Depends(get_database)):
    return ClientService(db).list_clients(user=user)


@router.patch("/{uid}", response_model=ClientSchema)
def update_client(
    uid: UUID4,
    client: NewClientSchema,
    user: User = Depends(user_check),
    db: DBSession = Depends(get_database),
):
    return ClientService(db).update_client(uid=uid, client=client)


@router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_client(
    uid: UUID4, user: User = Depends(staff_check), db: DBSession = Depends(get_database)
):
    return ClientService(db).delete_client(uid=uid)
