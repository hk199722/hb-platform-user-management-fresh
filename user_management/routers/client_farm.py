from fastapi import APIRouter, Depends, status
from pydantic import UUID4

from user_management.core.dependencies import DBSession, get_database
from user_management.schemas import ClientFarmSchema
from user_management.services.client_farm import ClientFarmService


router = APIRouter()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ClientFarmSchema)
def create_client_farm(new_client_farm: ClientFarmSchema, db: DBSession = Depends(get_database)):
    return ClientFarmService(db).create_client_farm(client_farm=new_client_farm)


@router.get("/{farm_uid}", response_model=ClientFarmSchema)
def get_client_farm(farm_uid: UUID4, db: DBSession = Depends(get_database)):
    return ClientFarmService(db).get_client_farm(farm_uid=farm_uid)
