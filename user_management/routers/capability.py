from typing import List

from fastapi import APIRouter, Depends, status

from user_management.core.dependencies import DBSession, get_database, staff_check, User, user_check
from user_management.repositories.base import Order
from user_management.schemas import CapabilitySchema, NewNamedEntitySchema
from user_management.services.capability import CapabilityService


router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CapabilitySchema)
def create_capability(
    new_capability: NewNamedEntitySchema,
    user: User = Depends(staff_check),  # pylint: disable=unused-argument
    db: DBSession = Depends(get_database),
):
    return CapabilityService(db).create_capability(capability=new_capability)


@router.get("/{capability_id}", response_model=CapabilitySchema)
def get_capability(
    capability_id: int,
    user: User = Depends(user_check),  # pylint: disable=unused-argument
    db: DBSession = Depends(get_database),
):
    return CapabilityService(db).get_capability(capability_id=capability_id)


@router.get("", response_model=List[CapabilitySchema])
def list_capabilities(
    order: Order = None,
    user: User = Depends(user_check),  # pylint: disable=unused-argument
    db: DBSession = Depends(get_database),
):
    return CapabilityService(db).list_capabilities(order_by=order)
