from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import UUID4

from user_management.core.dependencies import DBSession, get_database, get_user, User
from user_management.schemas import GCPUserSchema, NewGCPUserSchema, UpdateGCPUserSchema
from user_management.services.gcp_user import GCPUserService


router = APIRouter()

# FIXME: Remove this Pylint control line when filtering by permissions is finished.
# pylint: disable=unused-argument


# TODO: Implement assignation of user to a client:
#   - Only create users that belong to the Clients the request user is a member of.
#   - Create users for any Client if the request user is a HB Staff user.
@router.post("", status_code=status.HTTP_201_CREATED, response_model=GCPUserSchema)
def create_gcp_user(
    new_gcp_user: NewGCPUserSchema,
    user: User = Depends(get_user),
    db: DBSession = Depends(get_database),
):
    return GCPUserService(db).create_gcp_user(gcp_user=new_gcp_user)


# TODO: Filter users by only those that the request user can see:
#   - Only the users that belong to the Clients the request user is a member of.
#   - All users if the request user is a HB Staff user.
@router.get("/{uid}", response_model=GCPUserSchema)
def get_gcp_user(uid: UUID4, user: User = Depends(get_user), db: DBSession = Depends(get_database)):
    return GCPUserService(db).get_gcp_user(uid=uid)


@router.get("", response_model=List[GCPUserSchema])
def list_gcp_users(user: User = Depends(get_user), db: DBSession = Depends(get_database)):
    return GCPUserService(db).list_gcp_users(user=user)


# TODO: Update only those GCPUsers that the request user can see:
#   - Only the users that belong to the Clients the request user is a member of.
#   - All users if the request user is a HB Staff user.
@router.patch("/{uid}", response_model=GCPUserSchema)
def update_gcp_user(
    uid: UUID4,
    gcp_user: UpdateGCPUserSchema,
    user: User = Depends(get_user),
    db: DBSession = Depends(get_database),
):
    return GCPUserService(db).update_gcp_user(uid=uid, gcp_user=gcp_user)


# TODO: Delete only those GCPUsers that the request user can see:
#   - Only the users that belong to the Clients the request user is a member of.
#   - All users if the request user is a HB Staff user.
@router.delete("/{uid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gcp_user(
    uid: UUID4, user: User = Depends(get_user), db: DBSession = Depends(get_database)
):
    return GCPUserService(db).delete_gcp_user(uid=uid)


# TODO: Delete Roles for only those GCPUsers that the request user can see:
#   - Only the users that belong to the Clients the request user is a member of.
#   - All users if the request user is a HB Staff user.
@router.delete("/{uid}/roles/{client_uid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_gcp_user_role(
    uid: UUID4,
    client_uid: UUID4,
    user: User = Depends(get_user),
    db: DBSession = Depends(get_database),
):
    return GCPUserService(db).delete_gcp_user_role(uid=uid, client_uid=client_uid)
