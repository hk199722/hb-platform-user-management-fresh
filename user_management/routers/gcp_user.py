from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import UUID4

from user_management.core.dependencies import DBSession, get_database
from user_management.schemas import GCPUserSchema, NewGCPUserSchema
from user_management.services.gcp_user import GCPUserService


router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=GCPUserSchema)
def create_gcp_user(new_gcp_user: NewGCPUserSchema, db: DBSession = Depends(get_database)):
    return GCPUserService(db).create_gcp_user(gcp_user=new_gcp_user)


@router.get("/{uid}", response_model=GCPUserSchema)
def get_gcp_user(uid: UUID4, db: DBSession = Depends(get_database)):
    return GCPUserService(db).get_gcp_user(uid=uid)


@router.get("", response_model=List[GCPUserSchema])
def list_gcp_users(db: DBSession = Depends(get_database)):
    return GCPUserService(db).list_gcp_users()


@router.patch("/{uid}", response_model=GCPUserSchema)
def update_gcp_user(uid: UUID4, gcp_user: NewGCPUserSchema, db: DBSession = Depends(get_database)):
    return GCPUserService(db).update_gcp_user(uid=uid, gcp_user=gcp_user)


@router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gcp_user(uid: UUID4, db: DBSession = Depends(get_database)):
    return GCPUserService(db).delete_gcp_user(uid=uid)
