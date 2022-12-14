from typing import List

from fastapi import APIRouter, Depends, Response, status
from pydantic import EmailStr, UUID4

from user_management.core.dependencies import DBSession, get_database, user_check, User
from user_management.schemas import (
    CreatePasswordSchema,
    GCPUserSchema,
    NewGCPUserSchema,
    UpdateGCPUserSchema,
)
from user_management.services import GCPUserService, MailerService


router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=GCPUserSchema)
async def create_gcp_user(
    new_gcp_user: NewGCPUserSchema,
    user: User = Depends(user_check),
    db: DBSession = Depends(get_database),
):
    gcp_user = GCPUserService(db).create_gcp_user(gcp_user=new_gcp_user, user=user)
    MailerService(db).welcome_message(gcp_user_uid=gcp_user.uid)

    return gcp_user


@router.get("/{uid}", response_model=GCPUserSchema)
async def get_gcp_user(
    uid: UUID4, user: User = Depends(user_check), db: DBSession = Depends(get_database)
):
    return GCPUserService(db).get_gcp_user(uid=uid, user=user)


@router.get("", response_model=List[GCPUserSchema])
async def list_gcp_users(user: User = Depends(user_check), db: DBSession = Depends(get_database)):
    return GCPUserService(db).list_gcp_users(user=user)


@router.patch("/{uid}", response_model=GCPUserSchema)
async def update_gcp_user(
    uid: UUID4,
    gcp_user: UpdateGCPUserSchema,
    user: User = Depends(user_check),
    db: DBSession = Depends(get_database),
):
    return GCPUserService(db).update_gcp_user(uid=uid, gcp_user=gcp_user, user=user)


@router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_gcp_user(
    uid: UUID4, user: User = Depends(user_check), db: DBSession = Depends(get_database)
):
    return GCPUserService(db).delete_gcp_user(uid=uid, user=user)


@router.delete(
    "/{uid}/roles/{client_uid}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_gcp_user_role(
    uid: UUID4,
    client_uid: UUID4,
    user: User = Depends(user_check),
    db: DBSession = Depends(get_database),
):
    return GCPUserService(db).delete_gcp_user_role(uid=uid, client_uid=client_uid, user=user)


@router.post(
    "/{gcp_user_uid}/create-password/{security_token}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def create_gcp_user_password(
    gcp_user_uid: UUID4,
    security_token: UUID4,
    password: CreatePasswordSchema,
    db: DBSession = Depends(get_database),
):
    GCPUserService(db).set_user_password(
        uid=gcp_user_uid, token=security_token, password=password.password.get_secret_value()
    )


@router.get(
    "/{email}/reset-password", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def reset_gcp_user_password(email: EmailStr, db: DBSession = Depends(get_database)):
    MailerService(db).reset_password_message(gcp_user_email=email)
