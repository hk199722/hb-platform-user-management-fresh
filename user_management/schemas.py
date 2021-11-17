from pydantic import BaseModel, EmailStr, UUID4, validator


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


class GCPUserSchema(NamedModel):
    uid: UUID4
    email: EmailStr
    phone_number: str
    # TODO: roles

    class Config:
        orm_mode = True


class ClientFarmSchema(BaseModel):
    farm_uid: UUID4
    client_uid: UUID4

    class Config:
        orm_mode = True
