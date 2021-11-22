from typing import List, Optional

from pydantic import BaseModel, EmailStr, UUID4, validator

from user_management.models import Role


class NamedModel(BaseModel):
    name: str

    @validator("name", pre=True, always=True)
    def empty_string(cls, value):  # pylint: disable=no-self-argument
        return value if value != "" else None


class ClientSchema(NamedModel):
    uid: UUID4

    class Config:
        orm_mode = True


class NewClientSchema(NamedModel):
    pass


class ClientUserSchema(BaseModel):
    client_uid: UUID4
    role: Role

    class Config:
        orm_mode = True


class GCPUserSchema(NamedModel):
    uid: UUID4
    email: EmailStr
    phone_number: str
    clients: List[ClientUserSchema]

    class Config:
        orm_mode = True


class NewGCPUserSchema(NamedModel):
    email: EmailStr
    phone_number: str
    role: Optional[ClientUserSchema] = None


class ClientFarmSchema(BaseModel):
    farm_uid: UUID4
    client_uid: UUID4

    class Config:
        orm_mode = True
