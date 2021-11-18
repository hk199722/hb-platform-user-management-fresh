from fastapi import APIRouter, Depends, status

from user_management.core.dependencies import DBSession, get_database
from user_management.schemas import GCPUserSchema, NewGCPUserSchema
from user_management.services.gcp_user import GCPUserService


router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=GCPUserSchema)
def create_gcp_user(new_gcp_user: NewGCPUserSchema, db: DBSession = Depends(get_database)):
    return GCPUserService(db).create_gcp_user(gcp_user=new_gcp_user)
