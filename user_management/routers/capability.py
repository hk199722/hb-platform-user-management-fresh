from fastapi import APIRouter, Depends, status

from user_management.core.dependencies import DBSession, get_database, staff_check, User
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
